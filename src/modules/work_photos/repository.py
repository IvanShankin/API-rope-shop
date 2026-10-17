from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseIndexedRepository
from src.modules.work_photos.models import WorkPhoto
from src.modules.work_photos.models_dto import WorkPhotoBaseDTO


class WorkPhotoRepository(BaseIndexedRepository):
    """Репозиторий для работы с фотографиями работ (WorkPhoto)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=WorkPhoto)

    def add_photo(
        self, data: Union[WorkPhotoBaseDTO, dict, Any]
    ) -> WorkPhoto:
        """Добавление новой записи фотографии работы."""
        return self.add(data)

    async def get_by_id(self, photo_id: int) -> Optional[WorkPhoto]:
        """Получение фотографии работы по ID."""
        stmt = select(WorkPhoto).where(WorkPhoto.id == photo_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[WorkPhoto]:
        """Получение списка всех фотографий работ, отсортированных по index."""
        stmt = select(WorkPhoto).order_by(WorkPhoto.index)
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
        stmt = (
            update(WorkPhoto)
            .where(WorkPhoto.id == photo_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_photo(self, photo_id: int) -> None:
        """Удаление записи фотографии работы по ID."""
        stmt = delete(WorkPhoto).where(WorkPhoto.id == photo_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, photo_id: int) -> bool:
        """Проверка зависимостей (WorkPhoto не имеет дочерних связей)."""
        return False
