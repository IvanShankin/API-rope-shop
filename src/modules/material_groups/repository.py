from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.material_groups.models import MaterialGroup, MaterialGroupTranslation
from src.modules.materials.models import Material
from src.modules.rope_products.models import RopeProduct


class MaterialGroupRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MaterialGroup)

    async def add_group(self, data: Union[dict, Any]) -> MaterialGroup:
        """Добавление новой группы."""
        return self.add(data)

    async def get_all(self, is_active: Optional[bool] = None) -> Sequence[MaterialGroup]:
        """Получение всех групп материалов с их переводами, упорядоченных по index."""
        stmt = (
            select(MaterialGroup)
            .options(selectinload(MaterialGroup.translations))
            .order_by(MaterialGroup.index)
        )
        if is_active is not None:
            stmt = stmt.where(MaterialGroup.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_group_id(self, group_id: int) -> MaterialGroup | None:
        """Получение группы по ID с переводами."""
        stmt = (
            select(MaterialGroup)
            .options(selectinload(MaterialGroup.translations))
            .where(MaterialGroup.id == group_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> MaterialGroup | None:
        """Получение группы по уникальному коду."""
        stmt = (
            select(MaterialGroup)
            .options(selectinload(MaterialGroup.translations))
            .where(MaterialGroup.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_dependencies(self, group_id: int) -> bool:
        """Проверка наличия связей (материалы или привязанные веревки)."""
        materials_exist_stmt = select(exists().where(Material.material_group_id == group_id))
        ropes_exist_stmt = select(exists().where(RopeProduct.material_group_id == group_id))

        has_materials = await self.session.scalar(materials_exist_stmt)
        has_ropes = await self.session.scalar(ropes_exist_stmt)

        return bool(has_materials or has_ropes)

    async def update_group(self, group_id: int, update_data: dict) -> None:
        """Обновление полей группы."""
        stmt = update(MaterialGroup).where(MaterialGroup.id == group_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_group(self, group_id: int) -> None:
        """Удаление группы."""
        stmt = delete(MaterialGroup).where(MaterialGroup.id == group_id)
        await self.session.execute(stmt)


class MaterialGroupTranslationRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MaterialGroupTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> MaterialGroupTranslation:
        """Добавление перевода группы материалов."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> MaterialGroupTranslation | None:
        """Получение перевода по ID."""
        stmt = select(MaterialGroupTranslation).where(MaterialGroupTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_group_and_locale(
        self,
        group_id: int,
        locale: Language,
    ) -> MaterialGroupTranslation | None:
        """Получение перевода для конкретной группы и языка."""
        stmt = select(MaterialGroupTranslation).where(
            MaterialGroupTranslation.material_group_id == group_id,
            MaterialGroupTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода."""
        stmt = (
            update(MaterialGroupTranslation)
            .where(MaterialGroupTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода."""
        stmt = delete(MaterialGroupTranslation).where(MaterialGroupTranslation.id == translation_id)
        await self.session.execute(stmt)
