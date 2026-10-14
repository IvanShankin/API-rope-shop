from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.categories.repository import CategoryRepository
from src.modules.products.exception import (
    ProductAlreadyExists,
    ProductCategoryNotFound,
    ProductHasDependencies,
    ProductNotFound,
    ProductTranslationAlreadyExists,
    ProductTranslationDeleteError,
    ProductTranslationNotFound,
)
from src.modules.products.models import Product
from src.modules.products.models_dto import (
    ProductBase,
    ProductCreate,
    ProductLocalizedResponseDTO,
    ProductResponseDTO,
    ProductTranslationCreate,
    ProductTranslationInsert,
    ProductTranslationResponseDTO,
    ProductTranslationUpdate,
    ProductUpdate,
    ProductUpdateIndexDTO,
)
from src.modules.products.repository import (
    ProductRepository,
    ProductTranslationRepository,
)


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        translation_repo: ProductTranslationRepository,
        category_repo: CategoryRepository,
        session: AsyncSession,
    ):
        self.product_repo = product_repo
        self.translation_repo = translation_repo
        self.category_repo = category_repo
        self.session = session

    async def create_product(self, data: ProductCreate) -> ProductResponseDTO:
        """Создание нового товара с переводами."""
        if not data.translations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one translation is required when creating a Product.",
            )

        locales = [t.locale for t in data.translations]
        if len(locales) != len(set(locales)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate locales found in translations.",
            )

        # Проверка существования категории
        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise ProductCategoryNotFound(
                f"Category with id {data.category_id} not found."
            )

        # Проверка уникальности slug
        existing = await self.product_repo.get_by_slug(data.slug)
        if existing:
            raise ProductAlreadyExists(
                f"Product with slug '{data.slug}' already exists."
            )

        if data.index is None:
            max_index = await self.product_repo.get_max_index()
            target_index = max_index + 1
        else:
            target_index = data.index
            await self.product_repo.shift_indexes_for_insert(target_index=target_index)

        base_dto = ProductBase(
            category_id=data.category_id,
            slug=data.slug,
            product_type=data.product_type,
            index=target_index,
            is_active=data.is_active,
        )
        new_product = await self.product_repo.add_product(base_dto)
        await self.session.flush()

        for trans_data in data.translations:
            insert_dto = ProductTranslationInsert(
                locale=trans_data.locale,
                name=trans_data.name,
                description=trans_data.description,
                product_id=new_product.id,
            )
            await self.translation_repo.add_translation(insert_dto)

        await self.session.commit()
        created = await self.product_repo.get_by_id(new_product.id)
        return ProductResponseDTO.model_validate(created)

    async def get_all_products(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        product_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        locale: Optional[Language] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[ProductLocalizedResponseDTO]:
        """Получение списка товаров с фильтрацией, пагинацией и локализацией."""
        products = await self.product_repo.get_all(
            category_id=category_id,
            category_slug=category_slug,
            product_type=product_type,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

        return [self._to_localized_dto(p, locale) for p in products]

    async def get_product_by_id(self, product_id: int) -> ProductResponseDTO:
        """Получение товара по ID со всеми переводами и изображениями."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")
        return ProductResponseDTO.model_validate(product)

    async def get_product_by_slug(self, slug: str) -> ProductResponseDTO:
        """Получение товара по slug со всеми переводами и изображениями."""
        product = await self.product_repo.get_by_slug(slug)
        if not product:
            raise ProductNotFound(f"Product with slug '{slug}' not found.")
        return ProductResponseDTO.model_validate(product)

    async def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
    ) -> ProductResponseDTO:
        """Обновление атрибутов товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        if data.category_id is not None and data.category_id != product.category_id:
            category = await self.category_repo.get_by_id(data.category_id)
            if not category:
                raise ProductCategoryNotFound(
                    f"Category with id {data.category_id} not found."
                )

        if data.slug is not None and data.slug != product.slug:
            existing = await self.product_repo.get_by_slug(data.slug)
            if existing:
                raise ProductAlreadyExists(
                    f"Product with slug '{data.slug}' already exists."
                )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.product_repo.update_product(product_id, update_data)
        await self.session.commit()

        updated = await self.product_repo.get_by_id(product_id)
        return ProductResponseDTO.model_validate(updated)

    async def reorder_product(
        self,
        product_id: int,
        data: ProductUpdateIndexDTO,
    ) -> ProductResponseDTO:
        """Изменение порядкового индекса товара с автоматическим сдвигом соседей."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        if product.index != data.new_index:
            await self.product_repo.reorder_index(
                obj_id=product_id,
                old_index=product.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated = await self.product_repo.get_by_id(product_id)
        return ProductResponseDTO.model_validate(updated)

    async def delete_product(self, product_id: int) -> None:
        """Удаление товара с проверкой связанных сущностей."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        has_deps = await self.product_repo.has_dependencies(product_id)
        if has_deps:
            raise ProductHasDependencies(
                f"Cannot delete Product with id {product_id} because it is referenced by other entities."
            )

        await self.product_repo.delete_product(product_id)
        await self.product_repo.shift_indexes_after_delete(product.index)
        await self.session.commit()

    async def create_translation(
        self,
        product_id: int,
        data: ProductTranslationCreate,
    ) -> ProductTranslationResponseDTO:
        """Добавление перевода для товара."""
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFound(f"Product with id {product_id} not found.")

        existing = await self.translation_repo.get_by_product_and_locale(
            product_id=product_id,
            locale=data.locale,
        )
        if existing:
            raise ProductTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for product {product_id}."
            )

        insert_dto = ProductTranslationInsert(
            locale=data.locale,
            name=data.name,
            description=data.description,
            product_id=product_id,
        )
        trans = await self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        return ProductTranslationResponseDTO.model_validate(trans)

    async def update_translation(
        self,
        translation_id: int,
        data: ProductTranslationUpdate,
    ) -> ProductTranslationResponseDTO:
        """Обновление перевода товара."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise ProductTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise NoDataForUpdate("Did not transmit data")

        await self.translation_repo.update_translation(translation_id, update_data)
        await self.session.commit()

        updated = await self.translation_repo.get_by_id(translation_id)
        return ProductTranslationResponseDTO.model_validate(updated)

    async def delete_translation(
        self,
        translation_id: int,
    ) -> None:
        """Удаление перевода товара (с запретом удаления последнего)."""
        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans:
            raise ProductTranslationNotFound(
                f"Translation with id {translation_id} not found."
            )

        count = await self.translation_repo.count_by_product_id(trans.product_id)
        if count <= 1:
            raise ProductTranslationDeleteError(
                "Cannot delete the only remaining translation of the product."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()

    def _to_localized_dto(
        self,
        product: Product,
        locale: Optional[Language],
    ) -> ProductLocalizedResponseDTO:
        """Конвертация в локализованное DTO с fallback-логикой."""
        target_locale = locale or Language.ENG
        name = product._get_field_with_translation(
            lambda t: t.name,
            target_locale,
            fallback=Language.GER,
        )
        description = product._get_field_with_translation(
            lambda t: t.description,
            target_locale,
            fallback=Language.GER,
        )

        return ProductLocalizedResponseDTO(
            id=product.id,
            category_id=product.category_id,
            slug=product.slug,
            product_type=product.product_type,
            index=product.index,
            is_active=product.is_active,
            name=name if name else "No Translation",
            description=description,
            main_image_url=product.main_image_url,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
