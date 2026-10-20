from decimal import Decimal
from typing import Optional, Sequence, Union, Any, List

from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.splice_types.models import SpliceType


class SplicePriceRuleRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=SplicePriceRule)

    async def add_rule(self, data: Union[dict, Any]) -> SplicePriceRule:
        """Добавление нового ценового правила."""
        return self.add(data)

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        is_admin: bool = False,
    ) -> Sequence[SplicePriceRule]:
        """Получение всех правил с предзагрузкой связей."""
        stmt = (
            select(SplicePriceRule)
            .join(SplicePriceRule.splice_type)
            .options(
                selectinload(SplicePriceRule.splice_type).selectinload(SpliceType.translations),
                selectinload(SplicePriceRule.splice_material)
            )
        )
        if not is_admin:
            stmt = stmt.where(
                SplicePriceRule.is_active == True,
                SpliceType.is_active == True,
            )
        elif is_active is not None:
            stmt = stmt.where(SplicePriceRule.is_active == is_active)
            
        stmt = stmt.order_by(SplicePriceRule.diameter_from_mm.asc().nulls_first())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, rule_id: int) -> SplicePriceRule | None:
        """Получение правила по ID."""
        stmt = select(SplicePriceRule).options(
            selectinload(SplicePriceRule.splice_type).selectinload(SpliceType.translations),
            selectinload(SplicePriceRule.splice_material)
        ).where(SplicePriceRule.id == rule_id)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_applicable_rules(
        self,
        material_id: int,
        diameter: float,
        splice_type_ids: Optional[List[int]] = None
    ) -> Sequence[SplicePriceRule]:
        """
        Ищет подходящие ценовые правила для заданного материала и диаметра.
        Если передан список splice_type_ids, фильтрует только по ним (например, разрешенным для данной веревки).
        Используется в конфигураторе для отображения списка доступных услуг и их цен.
        """
        stmt = (
            select(SplicePriceRule)
            .join(SplicePriceRule.splice_type)
            .options(
                selectinload(SplicePriceRule.splice_type).selectinload(SpliceType.translations)
            )
            .where(
                SplicePriceRule.splice_material_id == material_id,
                SplicePriceRule.is_active == True,
                SpliceType.is_active == True,
                or_(
                    SplicePriceRule.diameter_from_mm.is_(None),
                    SplicePriceRule.diameter_from_mm <= diameter
                ),
                or_(
                    SplicePriceRule.diameter_to_mm.is_(None),
                    SplicePriceRule.diameter_to_mm >= diameter
                )
            )
        )
        
        if splice_type_ids is not None:
            stmt = stmt.where(SplicePriceRule.splice_type_id.in_(splice_type_ids))
            
        stmt = stmt.order_by(SplicePriceRule.diameter_from_mm.asc().nulls_first())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_price(
        self,
        material_id: int,
        type_id: int,
        diameter: float
    ) -> Decimal | None:
        """
        Универсальная функция расчета цены за конкретную услугу.
        Возвращает цену (Decimal) или None, если правило не найдено.
        Полностью соответствует логике calculate_splice_price из configurators_logic.md.
        """
        stmt = (
            select(SplicePriceRule.price)
            .join(SplicePriceRule.splice_type)
            .where(
                SplicePriceRule.splice_material_id == material_id,
                SplicePriceRule.splice_type_id == type_id,
                SplicePriceRule.is_active == True,
                SpliceType.is_active == True,
                or_(
                    SplicePriceRule.diameter_from_mm.is_(None),
                    SplicePriceRule.diameter_from_mm <= diameter
                ),
                or_(
                    SplicePriceRule.diameter_to_mm.is_(None),
                    SplicePriceRule.diameter_to_mm >= diameter
                )
            )
            .order_by(
                SplicePriceRule.diameter_from_mm.desc().nullslast(),
                SplicePriceRule.id.desc()
            )
            .limit(1)
        )
        
        result = await self.session.execute(stmt)
        price = result.scalars().first()
        return Decimal(str(price)) if price is not None else None

    async def update_rule(self, rule_id: int, update_data: dict) -> None:
        """Обновление ценового правила."""
        stmt = update(SplicePriceRule).where(SplicePriceRule.id == rule_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_rule(self, rule_id: int) -> None:
        """Удаление ценового правила."""
        stmt = delete(SplicePriceRule).where(SplicePriceRule.id == rule_id)
        await self.session.execute(stmt)
