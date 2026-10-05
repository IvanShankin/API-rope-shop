from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository
from src.modules.material_groups.models import MaterialGroup


class MaterialGroupRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MaterialGroup)

    async def add_group(self, data: Union[dict, Any]) -> MaterialGroup:
        """Добавление новой группы."""
        return self.add(data)

    async def get_all(self, is_active: Optional[bool] = None) -> Sequence[MaterialGroup]:
        """Получение всех групп материалов с их переводами."""
        stmt = select(MaterialGroup).options(
            selectinload(MaterialGroup.translations)
        )
        if is_active is not None:
            stmt = stmt.where(MaterialGroup.is_active == is_active)
        
        stmt = stmt.order_by(MaterialGroup.index)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_group_id(self, group_id: int) -> MaterialGroup | None:
        """Получение группы по ID."""
        stmt = select(MaterialGroup).options(
            selectinload(MaterialGroup.translations)
        ).where(MaterialGroup.id == group_id)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> MaterialGroup | None:
        """Получение группы по уникальному коду."""
        stmt = select(MaterialGroup).options(
            selectinload(MaterialGroup.translations)
        ).where(MaterialGroup.code == code)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_group(self, group_id: int, update_data: dict) -> None:
        """Обновление полей группы."""
        stmt = update(MaterialGroup).where(MaterialGroup.id == group_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_group(self, group_id: int) -> None:
        """Удаление группы."""
        stmt = delete(MaterialGroup).where(MaterialGroup.id == group_id)
        await self.session.execute(stmt)
