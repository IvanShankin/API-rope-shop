from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.categories.models import Category, CategoryTranslation
from src.modules.products.models import Product


class CategoryRepository(BaseIndexedRepository):
    """Репозиторий для категорий товаров."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Category)

    async def add_category(self, data: Union[dict, Any]) -> Category:
        """Добавление новой категории."""
        return self.add(data)

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[Category]:
        """Получение списка всех категорий с предзагрузкой переводов."""
        stmt = select(Category).options(selectinload(Category.translations))

        if is_active is not None:
            stmt = stmt.where(Category.is_active == is_active)

        stmt = stmt.order_by(Category.index)

        if skip > 0:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, category_id: int) -> Category | None:
        """Получение категории по ID с предзагрузкой переводов."""
        stmt = (
            select(Category)
            .options(selectinload(Category.translations))
            .where(Category.id == category_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        """Получение категории по slug с предзагрузкой переводов."""
        stmt = (
            select(Category)
            .options(selectinload(Category.translations))
            .where(Category.slug == slug)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists(self, category_id: int) -> bool:
        """Проверка существования категории по ID."""
        stmt = select(exists().where(Category.id == category_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def has_dependencies(self, category_id: int) -> bool:
        """Проверка наличия связанных товаров у категории."""
        stmt = select(exists().where(Product.category_id == category_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def get_products_count(self, category_id: int) -> int:
        """Подсчет количества активных товаров в категории."""
        stmt = select(func.count(Product.id)).where(Product.category_id == category_id)
        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def update_category(self, category_id: int, update_data: dict) -> None:
        """Обновление характеристик категории."""
        stmt = (
            update(Category)
            .where(Category.id == category_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_category(self, category_id: int) -> None:
        """Удаление категории."""
        stmt = delete(Category).where(Category.id == category_id)
        await self.session.execute(stmt)


class CategoryTranslationRepository(BaseRepository):
    """Репозиторий для переводов категорий."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=CategoryTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> CategoryTranslation:
        """Добавление перевода категории."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> CategoryTranslation | None:
        """Получение перевода по ID."""
        stmt = select(CategoryTranslation).where(CategoryTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_category_and_locale(
        self,
        category_id: int,
        locale: Language,
    ) -> CategoryTranslation | None:
        """Получение перевода для конкретной категории и языка."""
        stmt = select(CategoryTranslation).where(
            CategoryTranslation.category_id == category_id,
            CategoryTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода категории."""
        stmt = (
            update(CategoryTranslation)
            .where(CategoryTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода категории."""
        stmt = delete(CategoryTranslation).where(CategoryTranslation.id == translation_id)
        await self.session.execute(stmt)
