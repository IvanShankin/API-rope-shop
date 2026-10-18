from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.charity_photos.models import CharityPhoto, CharityPhotoTranslation
from src.modules.charity_photos.models_dto import (
    CharityPhotoBaseDTO,
    CharityPhotoTranslationInsert,
)


class CharityPhotoRepository(BaseIndexedRepository):
    """Репозиторий для работы с фотографиями благотворительности (CharityPhoto)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=CharityPhoto)

    def add_photo(
        self, data: Union[CharityPhotoBaseDTO, dict, Any]
    ) -> CharityPhoto:
        """Добавление новой записи фотографии благотворительности."""
        if isinstance(data, dict):
            clean_data = {k: v for k, v in data.items() if k in ("image_url", "index", "is_active")}
            instance = CharityPhoto(**clean_data)
        elif hasattr(data, "model_dump"):
            dump = data.model_dump()
            clean_data = {k: v for k, v in dump.items() if k in ("image_url", "index", "is_active")}
            instance = CharityPhoto(**clean_data)
        else:
            instance = CharityPhoto(
                image_url=getattr(data, "image_url", ""),
                index=getattr(data, "index", 0),
                is_active=getattr(data, "is_active", True),
            )
        self.session.add(instance)
        return instance

    async def get_by_id(self, photo_id: int) -> Optional[CharityPhoto]:
        """Получение фотографии благотворительности по ID с загрузкой переводов."""
        stmt = (
            select(CharityPhoto)
            .where(CharityPhoto.id == photo_id)
            .options(selectinload(CharityPhoto.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[CharityPhoto]:
        """Получение списка всех фотографий благотворительности, отсортированных по index и id."""
        stmt = (
            select(CharityPhoto)
            .options(selectinload(CharityPhoto.translations))
            .order_by(CharityPhoto.index.asc(), CharityPhoto.id.asc())
        )
        if is_active is not None:
            stmt = stmt.where(CharityPhoto.is_active == is_active)
        if skip > 0:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, is_active: Optional[bool] = None) -> int:
        """Подсчет количества фотографий благотворительности."""
        stmt = select(func.count(CharityPhoto.id))
        if is_active is not None:
            stmt = stmt.where(CharityPhoto.is_active == is_active)
        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def update_photo(self, photo_id: int, update_data: dict) -> None:
        """Обновление атрибутов фотографии благотворительности по ID."""
        clean_update = {k: v for k, v in update_data.items() if k in ("image_url", "index", "is_active")}
        if clean_update:
            stmt = (
                update(CharityPhoto)
                .where(CharityPhoto.id == photo_id)
                .values(**clean_update)
            )
            await self.session.execute(stmt)

    async def delete_photo(self, photo_id: int) -> None:
        """Удаление записи фотографии благотворительности по ID."""
        stmt = delete(CharityPhoto).where(CharityPhoto.id == photo_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, photo_id: int) -> bool:
        """Проверка зависимостей (CharityPhoto не имеет блокирующих внешних связей)."""
        return False


class CharityPhotoTranslationRepository(BaseRepository):
    """Репозиторий для работы с переводами фотографий благотворительности."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=CharityPhotoTranslation)

    def add_translation(
        self, data: Union[CharityPhotoTranslationInsert, dict, Any]
    ) -> CharityPhotoTranslation:
        """Добавление перевода фотографии благотворительности."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> Optional[CharityPhotoTranslation]:
        """Получение перевода по ID."""
        stmt = select(CharityPhotoTranslation).where(CharityPhotoTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_photo_id_and_locale(
        self, photo_id: int, locale: Language
    ) -> Optional[CharityPhotoTranslation]:
        """Получение перевода по ID фотографии благотворительности и локали."""
        stmt = select(CharityPhotoTranslation).where(
            CharityPhotoTranslation.charity_photo_id == photo_id,
            CharityPhotoTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(
        self, translation_id: int, update_data: dict
    ) -> None:
        """Обновление перевода по ID."""
        stmt = (
            update(CharityPhotoTranslation)
            .where(CharityPhotoTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода по ID."""
        stmt = delete(CharityPhotoTranslation).where(
            CharityPhotoTranslation.id == translation_id
        )
        await self.session.execute(stmt)

    async def count_by_photo_id(self, photo_id: int) -> int:
        """Подсчет количества переводов для конкретной фотографии благотворительности."""
        stmt = select(func.count(CharityPhotoTranslation.id)).where(
            CharityPhotoTranslation.charity_photo_id == photo_id
        )
        result = await self.session.scalar(stmt)
        return int(result or 0)
