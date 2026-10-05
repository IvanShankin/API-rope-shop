from typing import Sequence, Union, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.splice_materials.models import SpliceMaterial


class SpliceMaterialRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=SpliceMaterial)

    async def add_material(self, data: Union[dict, Any]) -> SpliceMaterial:
        """Добавление новой группы материалов для прайса."""
        return self.add(data)

    async def get_all(self) -> Sequence[SpliceMaterial]:
        """Получение всех групп материалов."""
        stmt = select(SpliceMaterial).order_by(SpliceMaterial.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, material_id: int) -> SpliceMaterial | None:
        """Получение группы материалов по ID."""
        stmt = select(SpliceMaterial).where(SpliceMaterial.id == material_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> SpliceMaterial | None:
        """Получение группы материалов по уникальному коду."""
        stmt = select(SpliceMaterial).where(SpliceMaterial.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_material(self, material_id: int, update_data: dict) -> None:
        """Обновление группы материалов."""
        stmt = update(SpliceMaterial).where(SpliceMaterial.id == material_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_material(self, material_id: int) -> None:
        """Удаление группы материалов."""
        stmt = delete(SpliceMaterial).where(SpliceMaterial.id == material_id)
        await self.session.execute(stmt)
