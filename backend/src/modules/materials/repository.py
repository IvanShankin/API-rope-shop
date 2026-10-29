from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.materials.models import Material, MaterialTranslation
from src.modules.material_groups.models import MaterialGroup


class MaterialRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Material)

    async def add_material(self, data: Union[dict, Any]) -> Material:
        """Добавление нового материала."""
        return self.add(data)

    async def get_all(
        self,
        material_group_id: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[Material]:
        """Получение списка всех материалов с фильтрацией и предзагрузкой переводов."""
        stmt = (
            select(Material)
            .options(selectinload(Material.translations))
            .order_by(Material.index.asc(), Material.id.asc())
        )
        if material_group_id is not None:
            stmt = stmt.where(Material.material_group_id == material_group_id)
        if is_active is not None:
            stmt = stmt.where(Material.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, material_id: int) -> Material | None:
        """Получение материала по ID с предзагрузкой переводов."""
        stmt = (
            select(Material)
            .options(selectinload(Material.translations))
            .where(Material.id == material_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Material | None:
        """Получение материала по уникальному коду."""
        stmt = (
            select(Material)
            .options(selectinload(Material.translations))
            .where(Material.code == code)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_material_group(self, material_group_id: int) -> bool:
        """Проверка существования группы материалов."""
        stmt = select(exists().where(MaterialGroup.id == material_group_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def has_dependencies(self, material_id: int) -> bool:
        """Проверка наличия связанных сущностей (правило 5.1)."""
        # На данный момент нет внешних таблиц, ссылающихся на materials.id кроме material_translations
        return False

    async def update_material(self, material_id: int, update_data: dict) -> None:
        """Обновление данных материала."""
        stmt = update(Material).where(Material.id == material_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_material(self, material_id: int) -> None:
        """Удаление материала."""
        stmt = delete(Material).where(Material.id == material_id)
        await self.session.execute(stmt)


class MaterialTranslationRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=MaterialTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> MaterialTranslation:
        """Добавление перевода материала."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> MaterialTranslation | None:
        """Получение перевода по ID."""
        stmt = select(MaterialTranslation).where(MaterialTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_material_and_locale(
        self,
        material_id: int,
        locale: Language
    ) -> MaterialTranslation | None:
        """Получение перевода для конкретного материала и языка."""
        stmt = select(MaterialTranslation).where(
            MaterialTranslation.material_id == material_id,
            MaterialTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода."""
        stmt = (
            update(MaterialTranslation)
            .where(MaterialTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода."""
        stmt = delete(MaterialTranslation).where(MaterialTranslation.id == translation_id)
        await self.session.execute(stmt)
