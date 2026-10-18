from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.work_photos.models import WorkPhoto, WorkPhotoTranslation
from src.modules.work_photos.models_dto import (
    WorkPhotoBaseDTO,
    WorkPhotoTranslationInsert,
)


class WorkPhotoRepository(BaseIndexedRepository):
    """Репозиторий для работы с фотографиями работ (WorkPhoto)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=WorkPhoto)

    def add_photo(
        self, data: Union[WorkPhotoBaseDTO, dict, Any]
    ) -> WorkPhoto:
        """Добавление новой записи фотографии работы."""
        if isinstance(data, dict):
            clean_data = {k: v for k, v in data.items() if k in ("image_url", "index", "is_active")}
            instance = WorkPhoto(**clean_data)
        elif hasattr(data, "model_dump"):
            dump = data.model_dump()
            clean_data = {k: v for k, v in dump.items() if k in ("image_url", "index", "is_active")}
            instance = WorkPhoto(**clean_data)
        else:
            instance = WorkPhoto(
                image_url=getattr(data, "image_url", ""),
                index=getattr(data, "index", 0),
                is_active=getattr(data, "is_active", True),
            )
        self.session.add(instance)
        return instance

    async def get_by_id(self, photo_id: int) -> Optional[WorkPhoto]:
        """Получение фотографии работы по ID с загрузкой переводов."""
        stmt = (
            select(WorkPhoto)
            .where(WorkPhoto.id == photo_id)
            .options(selectinload(WorkPhoto.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[WorkPhoto]:
        """Получение списка всех фотографий работ, отсортированных по index и id."""
        stmt = (
            select(WorkPhoto)
            .options(selectinload(WorkPhoto.translations))
            .order_by(WorkPhoto.index.asc(), WorkPhoto.id.asc())
        )
        if is_active is not None:
            stmt = stmt.where(WorkPhoto.is_active == is_active)
        if skip > 0:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, is_active: Optional[bool] = None) -> int:
        """Подсчет количества фотографий работ."""
        stmt = select(func.count(WorkPhoto.id))
        if is_active is not None:
            stmt = stmt.where(WorkPhoto.is_active == is_active)
        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def update_photo(self, photo_id: int, update_data: dict) -> None:
        """Обновление атрибутов фотографии работы по ID."""
        clean_update = {k: v for k, v in update_data.items() if k in ("image_url", "index", "is_active")}
        if clean_update:
            stmt = (
                update(WorkPhoto)
                .where(WorkPhoto.id == photo_id)
                .values(**clean_update)
            )
            await self.session.execute(stmt)

    async def delete_photo(self, photo_id: int) -> None:
        """Удаление записи фотографии работы по ID."""
        stmt = delete(WorkPhoto).where(WorkPhoto.id == photo_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, photo_id: int) -> bool:
        """Проверка зависимостей (WorkPhoto не имеет блокирующих внешних связей)."""
        return False


class WorkPhotoTranslationRepository(BaseRepository):
    """Репозиторий для работы с переводами фотографий работ."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=WorkPhotoTranslation)

    def add_translation(
        self, data: Union[WorkPhotoTranslationInsert, dict, Any]
    ) -> WorkPhotoTranslation:
        """Добавление перевода фотографии работы."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> Optional[WorkPhotoTranslation]:
        """Получение перевода по ID."""
        stmt = select(WorkPhotoTranslation).where(WorkPhotoTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_photo_id_and_locale(
        self, photo_id: int, locale: Language
    ) -> Optional[WorkPhotoTranslation]:
        """Получение перевода по ID фотографии работы и локали."""
        stmt = select(WorkPhotoTranslation).where(
            WorkPhotoTranslation.work_photo_id == photo_id,
            WorkPhotoTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(
        self, translation_id: int, update_data: dict
    ) -> None:
        """Обновление перевода по ID."""
        stmt = (
            update(WorkPhotoTranslation)
            .where(WorkPhotoTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода по ID."""
        stmt = delete(WorkPhotoTranslation).where(
            WorkPhotoTranslation.id == translation_id
        )
        await self.session.execute(stmt)

    async def count_by_photo_id(self, photo_id: int) -> int:
        """Подсчет количества переводов для конкретной фотографии работы."""
        stmt = select(func.count(WorkPhotoTranslation.id)).where(
            WorkPhotoTranslation.work_photo_id == photo_id
        )
        result = await self.session.scalar(stmt)
        return int(result or 0)
