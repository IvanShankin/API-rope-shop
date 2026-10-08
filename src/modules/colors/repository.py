from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.colors.models import Color, ColorTranslation
from src.modules.rope_products.models import RopeProductColor


class ColorRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Color)

    async def add_color(self, data: Union[dict, Any]) -> Color:
        """Добавление нового цвета."""
        return self.add(data)

    async def get_all(self, is_active: Optional[bool] = None) -> Sequence[Color]:
        """Получение списка всех цветов с предзагрузкой переводов."""
        stmt = select(Color).options(
            selectinload(Color.translations)
        )
        if is_active is not None:
            stmt = stmt.where(Color.is_active == is_active)

        stmt = stmt.order_by(Color.index)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, color_id: int) -> Color | None:
        """Получение цвета по ID."""
        stmt = select(Color).options(
            selectinload(Color.translations)
        ).where(Color.id == color_id)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Color | None:
        """Получение цвета по уникальному коду."""
        stmt = select(Color).options(
            selectinload(Color.translations)
        ).where(Color.code == code)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_dependencies(self, color_id: int) -> bool:
        """Проверка наличия связей (например, привязанные веревки)."""
        stmt = select(exists().where(RopeProductColor.color_id == color_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def update_color(self, color_id: int, update_data: dict) -> None:
        """Обновление данных цвета."""
        stmt = update(Color).where(Color.id == color_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_color(self, color_id: int) -> None:
        """Удаление цвета."""
        stmt = delete(Color).where(Color.id == color_id)
        await self.session.execute(stmt)


class ColorTranslationRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ColorTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> ColorTranslation:
        """Добавление перевода цвета."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> ColorTranslation | None:
        """Получение перевода по ID."""
        stmt = select(ColorTranslation).where(ColorTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_color_and_locale(self, color_id: int, locale: Language) -> ColorTranslation | None:
        """Получение перевода для конкретного цвета и языка."""
        stmt = select(ColorTranslation).where(
            ColorTranslation.color_id == color_id,
            ColorTranslation.locale == locale
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода."""
        stmt = update(ColorTranslation).where(ColorTranslation.id == translation_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода."""
        stmt = delete(ColorTranslation).where(ColorTranslation.id == translation_id)
        await self.session.execute(stmt)
