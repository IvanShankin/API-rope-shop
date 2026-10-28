from src.modules.products.models import Product
from typing import Sequence, Union, Any

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.rope_products.models import RopeConfiguratorSetting
from src.modules.splice_types.models import SpliceType


class SpliceMaterialRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=SpliceMaterial)

    async def add_material(self, data: Union[dict, Any]) -> SpliceMaterial:
        """Добавление новой группы материалов для прайса."""
        return self.add(data)

    async def get_all(
        self,
        include_rules: bool = False,
        is_active: Optional[bool] = None,
    ) -> Sequence[SpliceMaterial]:
        """Получение всех групп материалов."""
        stmt = select(SpliceMaterial).order_by(SpliceMaterial.id)
        if is_active is not None:
            stmt = stmt.where(SpliceMaterial.is_active == is_active)
        if include_rules:
            stmt = stmt.options(
                selectinload(SpliceMaterial.rules)
                .selectinload(SplicePriceRule.splice_type)
                .selectinload(SpliceType.translations)
            )
            
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(
        self,
        material_id: int,
        include_rules: bool = False,
        is_active: Optional[bool] = None,
    ) -> SpliceMaterial | None:
        """Получение группы материалов по ID."""
        stmt = select(SpliceMaterial).where(SpliceMaterial.id == material_id)
        if is_active is not None:
            stmt = stmt.where(SpliceMaterial.is_active == is_active)
        if include_rules:
            stmt = stmt.options(
                selectinload(SpliceMaterial.rules)
                .selectinload(SplicePriceRule.splice_type)
                .selectinload(SpliceType.translations)
            )
            
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> SpliceMaterial | None:
        """Получение группы материалов по уникальному коду."""
        stmt = select(SpliceMaterial).where(SpliceMaterial.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_dependencies(self, material_id: int) -> bool:
        """Проверка наличия связей (правила цен или привязанные веревки)."""
        rules_exist_stmt = select(exists().where(SplicePriceRule.splice_material_id == material_id))
        ropes_exist_stmt = select(exists().where(RopeConfiguratorSetting.splice_material_id == material_id))
        
        has_rules = await self.session.scalar(rules_exist_stmt)
        has_ropes = await self.session.scalar(ropes_exist_stmt)
        
        return bool(has_rules or has_ropes)

    async def get_dependencies(self, material_id: int) -> dict:
        """Получение списка зависимостей (правила цен и привязанные канаты)."""
        rules_stmt = (
            select(SplicePriceRule)
            .options(selectinload(SplicePriceRule.splice_type))
            .where(SplicePriceRule.splice_material_id == material_id)
            .order_by(SplicePriceRule.id)
        )
        rules = (await self.session.execute(rules_stmt)).scalars().all()

        ropes_stmt = (
            select(Product)
            .join(RopeConfiguratorSetting, RopeConfiguratorSetting.product_id == Product.id)
            .options(selectinload(Product.translations))
            .where(RopeConfiguratorSetting.splice_material_id == material_id)
            .order_by(Product.id)
        )
        ropes = (await self.session.execute(ropes_stmt)).scalars().all()

        return {
            "rules": rules,
            "ropes": ropes,
        }

    async def update_material(self, material_id: int, update_data: dict) -> None:
        """Обновление полей группы материалов."""
        stmt = update(SpliceMaterial).where(SpliceMaterial.id == material_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_material(self, material_id: int) -> None:
        """Удаление группы материалов."""
        stmt = delete(SpliceMaterial).where(SpliceMaterial.id == material_id)
        await self.session.execute(stmt)
