from typing import Optional, Sequence
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import (
    BaseIndexedRepository,
    BaseRepository,
)
from src.modules.categories.models import Category
from src.modules.product_images.models import ProductImage
from src.modules.products.models import Product, ProductTranslation
from src.modules.products.models_dto import (
    ProductBase,
    ProductTranslationInsert,
)
from src.modules.rope_products.models import RopeProduct


class ProductRepository(BaseIndexedRepository):
    def __init__(self, session):
        super().__init__(session=session, model=Product)

    async def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.translations),
                selectinload(Product.images),
                selectinload(Product.category),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        stmt = (
            select(Product)
            .where(Product.slug == slug)
            .options(
                selectinload(Product.translations),
                selectinload(Product.images),
                selectinload(Product.category),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        product_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[Product]:
        stmt = (
            select(Product)
            .options(
                selectinload(Product.translations),
                selectinload(Product.images),
                selectinload(Product.category),
            )
        )

        if category_slug is not None:
            stmt = stmt.join(Product.category).where(Category.slug == category_slug)

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if product_type is not None:
            stmt = stmt.where(Product.product_type == product_type)

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        stmt = stmt.order_by(Product.index).offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        product_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        stmt = select(func.count(Product.id))

        if category_slug is not None:
            stmt = stmt.join(Product.category).where(Category.slug == category_slug)

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if product_type is not None:
            stmt = stmt.where(Product.product_type == product_type)

        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def has_dependencies(self, product_id: int) -> bool:
        """Проверка наличия связанных записей в rope_products или product_images."""
        rope_stmt = select(exists().where(RopeProduct.product_id == product_id))
        images_stmt = select(exists().where(ProductImage.product_id == product_id))

        has_rope = (await self.session.execute(rope_stmt)).scalar() or False
        has_images = (await self.session.execute(images_stmt)).scalar() or False

        return has_rope or has_images

    async def add_product(self, data: ProductBase) -> Product:
        product = Product(
            category_id=data.category_id,
            slug=data.slug,
            product_type=data.product_type,
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
        stmt = delete(Product).where(Product.id == product_id)
        await self.session.execute(stmt)


class ProductTranslationRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session=session, model=ProductTranslation)

    async def add_translation(self, data: ProductTranslationInsert) -> ProductTranslation:
        trans = ProductTranslation(
            product_id=data.product_id,
            locale=data.locale,
            name=data.name,
            description=data.description,
        )
        self.session.add(trans)
        return trans

    async def get_by_id(self, translation_id: int) -> Optional[ProductTranslation]:
        stmt = select(ProductTranslation).where(ProductTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_and_locale(
        self,
        product_id: int,
        locale: Language,
    ) -> Optional[ProductTranslation]:
        stmt = select(ProductTranslation).where(
            ProductTranslation.product_id == product_id,
            ProductTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        stmt = (
            update(ProductTranslation)
            .where(ProductTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        stmt = delete(ProductTranslation).where(ProductTranslation.id == translation_id)
        await self.session.execute(stmt)

    async def count_by_product_id(self, product_id: int) -> int:
        stmt = select(func.count(ProductTranslation.id)).where(
            ProductTranslation.product_id == product_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
