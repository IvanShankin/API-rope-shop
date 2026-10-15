from typing import Any, Optional, Sequence, Union
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.product_specification.models import (
    ProductSpecification,
    ProductSpecificationTranslation,
)


class ProductSpecificationRepository(BaseIndexedRepository):
    """Репозиторий для динамических характеристик товаров."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductSpecification)

    async def add_specification(self, product_id: int, index: int) -> ProductSpecification:
        """Добавление новой характеристики товара."""
        spec = ProductSpecification(product_id=product_id, index=index)
        self.session.add(spec)
        return spec

    async def get_by_id(self, spec_id: int) -> Optional[ProductSpecification]:
        """Получение характеристики по ID с предзагрузкой переводов."""
        stmt = (
            select(ProductSpecification)
            .where(ProductSpecification.id == spec_id)
            .options(selectinload(ProductSpecification.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_product(
        self, spec_id: int, product_id: int
    ) -> Optional[ProductSpecification]:
        """Получение характеристики по ID и product_id с предзагрузкой переводов."""
        stmt = (
            select(ProductSpecification)
            .where(
                ProductSpecification.id == spec_id,
                ProductSpecification.product_id == product_id,
            )
            .options(selectinload(ProductSpecification.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(
        self, product_id: int
    ) -> Sequence[ProductSpecification]:
        """Получение всех характеристик конкретного товара, отсортированных по индексу."""
        stmt = (
            select(ProductSpecification)
            .where(ProductSpecification.product_id == product_id)
            .options(selectinload(ProductSpecification.translations))
            .order_by(ProductSpecification.index)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_ids_and_product(
        self, spec_ids: Sequence[int], product_id: int
    ) -> Sequence[ProductSpecification]:
        """Получение характеристик по списку ID для конкретного товара."""
        stmt = (
            select(ProductSpecification)
            .where(
                ProductSpecification.id.in_(spec_ids),
                ProductSpecification.product_id == product_id,
            )
            .options(selectinload(ProductSpecification.translations))
            .order_by(ProductSpecification.index)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def exists(self, spec_id: int) -> bool:
        """Проверка существования характеристики по ID."""
        stmt = select(exists().where(ProductSpecification.id == spec_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def count_by_product_id(self, product_id: int) -> int:
        """Подсчет количества характеристик у товара."""
        stmt = select(func.count(ProductSpecification.id)).where(
            ProductSpecification.product_id == product_id
        )
        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def update_specification(self, spec_id: int, update_data: dict) -> None:
        """Обновление полей характеристики."""
        stmt = (
            update(ProductSpecification)
            .where(ProductSpecification.id == spec_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_specification(self, spec_id: int) -> None:
        """Удаление характеристики."""
        stmt = delete(ProductSpecification).where(ProductSpecification.id == spec_id)
        await self.session.execute(stmt)

    async def delete_by_ids_and_product(
        self, spec_ids: Sequence[int], product_id: int
    ) -> int:
        """Удаление нескольких характеристик конкретного товара. Возвращает количество удаленных записей."""
        stmt = (
            delete(ProductSpecification)
            .where(
                ProductSpecification.id.in_(spec_ids),
                ProductSpecification.product_id == product_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def delete_by_product_id(self, product_id: int) -> int:
        """Удаление всех характеристик товара."""
        stmt = delete(ProductSpecification).where(ProductSpecification.product_id == product_id)
        result = await self.session.execute(stmt)
        return result.rowcount or 0


class ProductSpecificationTranslationRepository(BaseRepository):
    """Репозиторий для переводов характеристик товаров."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductSpecificationTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> ProductSpecificationTranslation:
        """Добавление перевода характеристики."""
        return self.add(data)

    async def get_by_specification_and_locale(
        self, spec_id: int, locale: Language
    ) -> Optional[ProductSpecificationTranslation]:
        """Получение перевода по ID характеристики и языку."""
        stmt = select(ProductSpecificationTranslation).where(
            ProductSpecificationTranslation.specification_id == spec_id,
            ProductSpecificationTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_translation(
        self, spec_id: int, locale: Language, name: str, value: str
    ) -> ProductSpecificationTranslation:
        """Создание или обновление перевода для характеристики."""
        existing = await self.get_by_specification_and_locale(spec_id, locale)
        if existing:
            existing.name = name
            existing.value = value
            return existing

        translation = ProductSpecificationTranslation(
            specification_id=spec_id,
            locale=locale,
            name=name,
            value=value,
        )
        self.session.add(translation)
        return translation

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода по ID."""
        stmt = (
            update(ProductSpecificationTranslation)
            .where(ProductSpecificationTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода по ID."""
        stmt = delete(ProductSpecificationTranslation).where(
            ProductSpecificationTranslation.id == translation_id
        )
        await self.session.execute(stmt)

    async def delete_by_specification_id(self, spec_id: int) -> None:
        """Удаление всех переводов характеристики."""
        stmt = delete(ProductSpecificationTranslation).where(
            ProductSpecificationTranslation.specification_id == spec_id
        )
        await self.session.execute(stmt)

    async def count_by_specification_id(self, spec_id: int) -> int:
        """Подсчет количества переводов у характеристики."""
        stmt = select(func.count(ProductSpecificationTranslation.id)).where(
            ProductSpecificationTranslation.specification_id == spec_id
        )
        result = await self.session.scalar(stmt)
        return int(result or 0)
