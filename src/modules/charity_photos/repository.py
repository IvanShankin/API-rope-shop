from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseIndexedRepository
from src.modules.charity_photos.models import CharityPhoto
from src.modules.charity_photos.models_dto import CharityPhotoBaseDTO


class CharityPhotoRepository(BaseIndexedRepository):
    """Репозиторий для работы с фотографиями благотворительности (CharityPhoto)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=CharityPhoto)

    def add_photo(
        self, data: Union[CharityPhotoBaseDTO, dict, Any]
    ) -> CharityPhoto:
        """Добавление новой записи фотографии благотворительности."""
        return self.add(data)

    async def get_by_id(self, photo_id: int) -> Optional[CharityPhoto]:
        """Получение фотографии благотворительности по ID."""
        stmt = select(CharityPhoto).where(CharityPhoto.id == photo_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[CharityPhoto]:
        """Получение списка всех фотографий благотворительности, отсортированных по index."""
        stmt = select(CharityPhoto).order_by(CharityPhoto.index.asc(), CharityPhoto.id.asc())
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
        stmt = (
            update(CharityPhoto)
            .where(CharityPhoto.id == photo_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_photo(self, photo_id: int) -> None:
        """Удаление записи фотографии благотворительности по ID."""
        stmt = delete(CharityPhoto).where(CharityPhoto.id == photo_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, photo_id: int) -> bool:
        """Проверка зависимостей (CharityPhoto не имеет дочерних связей)."""
        return False
