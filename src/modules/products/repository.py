from typing import Any, List, Optional, Sequence, Union
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import (
    BaseIndexedRepository,
    BaseRepository,
)
from src.modules.categories.models import Category
from src.modules.products.models import Product, ProductTranslation
from src.modules.products.models_dto import (
    ProductBase,
    ProductTranslationInsert,
)


class ProductRepository(BaseIndexedRepository):
    def __init__(self, session):
        super().__init__(session=session, model=Product)

    @staticmethod
    def _default_product_options():
        from src.modules.colors.models import Color
        from src.modules.product_application.models import (
            ProductApplication,
            ProductAssignedApplication,
        )
        from src.modules.product_specification.models import ProductSpecification
        from src.modules.rope_product_color.models import ProductColor

        return [
            selectinload(Product.translations),
            selectinload(Product.images),
            selectinload(Product.category),
            selectinload(Product.specifications).selectinload(ProductSpecification.translations),
            selectinload(Product.assigned_applications)
            .selectinload(ProductAssignedApplication.application)
            .selectinload(ProductApplication.translations),
            selectinload(Product.variants),
            selectinload(Product.colors).selectinload(ProductColor.color).selectinload(Color.translations),
        ]

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(*self._default_product_options())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        stmt = (
            select(Product)
            .where(Product.slug == slug)
            .options(*self._default_product_options())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        product_type: Optional[str] = None,
        material_id: Optional[int] = None,
        construction_type: Optional[str] = None,
        application_codes: Optional[List[str]] = None,
        diameter_min: Optional[float] = None,
        diameter_max: Optional[float] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[Product]:
        from src.modules.product_application.models import (
            ProductApplication,
            ProductAssignedApplication,
        )
        from src.modules.rope_products.models import (
            ProductVariant,
            RopeConfiguratorSetting,
        )

        stmt = (
            select(Product)
            .options(*self._default_product_options())
            .order_by(Product.index)
        )

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if category_slug is not None:
            stmt = stmt.join(Product.category).where(Category.slug == category_slug)

        if product_type is not None:
            stmt = stmt.where(Product.product_type == product_type)

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        if construction_type is not None:
            stmt = stmt.where(Product.construction_type == construction_type)

        if material_id is not None:
            stmt = stmt.where(
                exists().where(
                    RopeConfiguratorSetting.product_id == Product.id,
                    RopeConfiguratorSetting.material_id == material_id,
                )
            )

        if application_codes:
            stmt = stmt.where(
                exists().where(
                    ProductAssignedApplication.product_id == Product.id,
                    ProductAssignedApplication.application_id == ProductApplication.id,
                    ProductApplication.code.in_(application_codes),
                )
            )

        if diameter_min is not None or diameter_max is not None:
            variant_conds = [
                ProductVariant.product_id == Product.id,
                ProductVariant.is_active.is_(True),
            ]
            if diameter_min is not None:
                variant_conds.append(ProductVariant.size_value >= diameter_min)
            if diameter_max is not None:
                variant_conds.append(ProductVariant.size_value <= diameter_max)
            stmt = stmt.where(exists().where(*variant_conds))\

        if skip:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def has_dependencies(self, product_id: int) -> bool:
        """
        Проверка наличия блокирующих внешних зависимостей перед удалением товара.

        Все дочерние сущности (ProductImage, ProductVariant, ProductSpecification,
        RopeConfiguratorSetting, ProductColor, RopeAllowedSplice, ProductAssignedApplication,
        ProductTranslation) удаляются каскадно/явно при удалении продукта (включая очистку медиафайлов).
        Внешние ссылки из заявок (QuoteRopeItem) имеют ON DELETE SET NULL согласно
        паттерну Order Snapshot и не блокируют удаление.
        Блокирующие внешние зависимости отсутствуют.
        """
        return False

    async def add_product(self, data: ProductBase) -> Product:
        product = Product(
            category_id=data.category_id,
            slug=data.slug,
            product_type=data.product_type,
            price_unit=data.price_unit,
            has_configurator=data.has_configurator,
            construction_type=data.construction_type,
            index=data.index,
            is_active=data.is_active,
        )
        self.session.add(product)
        return product

    async def update_product(self, product_id: int, update_data: dict) -> None:
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_product(self, product_id: int) -> None:
        """
        Удаление товара и очистка всех ссылающихся на него зависимых данных.
        Для QuoteRopeItem выполняется обнуление FK (ON DELETE SET NULL) для сохранения снимка заказа.
        """
        from src.modules.product_application.models import ProductAssignedApplication
        from src.modules.product_images.models import ProductImage
        from src.modules.product_specification.models import (
            ProductSpecification,
            ProductSpecificationTranslation,
        )
        from src.modules.products.models import ProductTranslation
        from src.modules.quote_requests.models import QuoteRopeItem
        from src.modules.rope_allowed_splice.models import RopeAllowedSplice
        from src.modules.rope_product_color.models import ProductColor
        from src.modules.rope_products.models import (
            ProductVariant,
            RopeConfiguratorSetting,
        )

        # 1. Обнуляем FK в QuoteRopeItem (согласно логике Order Snapshot)
        await self.session.execute(
            update(QuoteRopeItem)
            .where(QuoteRopeItem.product_id == product_id)
            .values(product_id=None)
        )

        # 2. Удаляем дочерние связанные сущности
        await self.session.execute(
            delete(ProductTranslation).where(ProductTranslation.product_id == product_id)
        )
        await self.session.execute(
            delete(ProductImage).where(ProductImage.product_id == product_id)
        )
        await self.session.execute(
            delete(ProductVariant).where(ProductVariant.product_id == product_id)
        )
        await self.session.execute(
            delete(ProductColor).where(ProductColor.product_id == product_id)
        )
        await self.session.execute(
            delete(RopeAllowedSplice).where(RopeAllowedSplice.product_id == product_id)
        )
        await self.session.execute(
            delete(RopeConfiguratorSetting).where(RopeConfiguratorSetting.product_id == product_id)
        )

        # Для спецификаций предварительно удаляем их переводы
        spec_ids_stmt = select(ProductSpecification.id).where(
            ProductSpecification.product_id == product_id
        )
        spec_ids = (await self.session.execute(spec_ids_stmt)).scalars().all()
        if spec_ids:
            await self.session.execute(
                delete(ProductSpecificationTranslation).where(
                    ProductSpecificationTranslation.specification_id.in_(spec_ids)
                )
            )
            await self.session.execute(
                delete(ProductSpecification).where(
                    ProductSpecification.id.in_(spec_ids)
                )
            )

        await self.session.execute(
            delete(ProductAssignedApplication).where(
                ProductAssignedApplication.product_id == product_id
            )
        )

        # 3. Удаляем сам продукт
        stmt = delete(Product).where(Product.id == product_id)
        await self.session.execute(stmt)


class ProductTranslationRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session=session, model=ProductTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> ProductTranslation:
        """Добавление перевода товара."""
        return self.add(data)

    async def get_by_product_and_locale(
        self, product_id: int, locale: Language
    ) -> Optional[ProductTranslation]:
        stmt = select(ProductTranslation).where(
            ProductTranslation.product_id == product_id,
            ProductTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_translation(
        self, product_id: int, data: ProductTranslationInsert
    ) -> ProductTranslation:
        existing = await self.get_by_product_and_locale(product_id, data.locale)
        if existing:
            existing.name = data.name
            existing.subtitle = data.subtitle
            existing.description = data.description
            return existing

        translation = ProductTranslation(
            product_id=product_id,
            locale=data.locale,
            name=data.name,
            subtitle=data.subtitle,
            description=data.description,
        )
        self.session.add(translation)
        return translation

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода товара."""
        stmt = (
            update(ProductTranslation)
            .where(ProductTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода товара."""
        stmt = delete(ProductTranslation).where(ProductTranslation.id == translation_id)
        await self.session.execute(stmt)

    async def count_by_product_id(self, product_id: int) -> int:
        """Количество переводов товара."""
        stmt = select(func.count(ProductTranslation.id)).where(ProductTranslation.product_id == product_id)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def delete_by_product_id(self, product_id: int) -> None:
        stmt = delete(ProductTranslation).where(
            ProductTranslation.product_id == product_id
        )
        await self.session.execute(stmt)
