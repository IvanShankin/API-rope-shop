from src.modules.base.exception import ServiceException
from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.splice_prices.repository import SplicePriceRuleRepository
from src.modules.splice_prices.models_dto import (
    SplicePriceRuleBatchRequest,
    SplicePriceRuleBatchResponseDTO,
    SplicePriceRuleCreate,
    SplicePriceRuleUpdate,
    SplicePriceRuleResponseDTO,
    SplicePriceRuleWithRelationsResponseDTO
)
from src.modules.splice_prices.exception import SplicePriceRuleNotFound, SplicePriceRuleValidationError


class SplicePriceRuleService:
    def __init__(
        self,
        rule_repo: SplicePriceRuleRepository,
        session: AsyncSession
    ):
        self.rule_repo = rule_repo
        self.session = session

    async def create_rule(self, data: SplicePriceRuleCreate) -> SplicePriceRuleResponseDTO:
        new_rule = await self.rule_repo.add_rule(data.model_dump())
        await self.session.commit()
        await self.session.refresh(new_rule)
        return SplicePriceRuleResponseDTO.model_validate(new_rule)

    async def get_all_rules(self, is_active: Optional[bool] = None, is_admin: bool = False) -> List[SplicePriceRuleWithRelationsResponseDTO]:
        effective_active = is_active if is_admin else True
        rules = await self.rule_repo.get_all(is_active=effective_active, is_admin=is_admin)
        return [SplicePriceRuleWithRelationsResponseDTO.model_validate(r) for r in rules]

    async def get_rule_by_id(self, rule_id: int, is_admin: bool = False) -> SplicePriceRuleWithRelationsResponseDTO:
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule or (not is_admin and (not rule.is_active or not rule.splice_type.is_active)):
            raise SplicePriceRuleNotFound(f"SplicePriceRule with id {rule_id} not found.")
        return SplicePriceRuleWithRelationsResponseDTO.model_validate(rule)

    async def get_applicable_rules(
        self, 
        material_id: int, 
        diameter: float, 
        splice_type_ids: Optional[List[int]] = None
    ) -> List[SplicePriceRuleWithRelationsResponseDTO]:
        rules = await self.rule_repo.get_applicable_rules(
            material_id=material_id, 
            diameter=diameter, 
            splice_type_ids=splice_type_ids
        )
        return [SplicePriceRuleWithRelationsResponseDTO.model_validate(r) for r in rules]

    async def update_rule(self, rule_id: int, data: SplicePriceRuleUpdate) -> SplicePriceRuleResponseDTO:
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise SplicePriceRuleNotFound(f"SplicePriceRule with id {rule_id} not found.")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            await self.rule_repo.update_rule(rule_id, update_data)
            await self.session.commit()
            
        updated_rule = await self.rule_repo.get_by_id(rule_id)
        return SplicePriceRuleResponseDTO.model_validate(updated_rule)

    async def delete_rule(self, rule_id: int) -> None:
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise SplicePriceRuleNotFound(f"SplicePriceRule with id {rule_id} not found.")
            
        await self.rule_repo.delete_rule(rule_id)
        await self.session.commit()

    async def batch_save_rules(self, data: SplicePriceRuleBatchRequest) -> SplicePriceRuleBatchResponseDTO:
        """Атомарное сохранение всей тарифной сетки (создание, обновление, удаление в одной транзакции)."""
        # 1. Валидация диапазона диаметров
        for item in data.rules:
            if item.diameter_from_mm is not None and item.diameter_to_mm is not None:
                if item.diameter_from_mm > item.diameter_to_mm:
                    raise SplicePriceRuleValidationError(
                        f"Invalid diameter range: diameter_from_mm ({item.diameter_from_mm}) cannot be greater than diameter_to_mm ({item.diameter_to_mm})."
                    )

        created_rules = []
        updated_rules = []
        deleted_count = 0

        try:
            # 2. Удаление правил
            if data.delete_rule_ids:
                for rule_id in data.delete_rule_ids:
                    existing = await self.rule_repo.get_by_id(rule_id)
                    if not existing:
                        raise SplicePriceRuleNotFound(f"SplicePriceRule with id {rule_id} not found.")
                    await self.rule_repo.delete_rule(rule_id)
                    deleted_count += 1

            # 3. Создание и обновление
            for item in data.rules:
                if item.id is not None:
                    existing = await self.rule_repo.get_by_id(item.id)
                    if not existing:
                        raise SplicePriceRuleNotFound(f"SplicePriceRule with id {item.id} not found.")
                    update_dict = item.model_dump(exclude={"id"})
                    await self.rule_repo.update_rule(item.id, update_dict)
                    refreshed = await self.rule_repo.get_by_id(item.id)
                    updated_rules.append(refreshed)
                else:
                    create_dict = item.model_dump(exclude={"id"})
                    new_rule = await self.rule_repo.add_rule(create_dict)
                    created_rules.append(new_rule)

            # 4. Атомарная фиксация всей транзакции
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        for r in created_rules:
            await self.session.refresh(r)

        all_rules = created_rules + updated_rules
        return SplicePriceRuleBatchResponseDTO(
            created_count=len(created_rules),
            updated_count=len(updated_rules),
            deleted_count=deleted_count,
            rules=[SplicePriceRuleResponseDTO.model_validate(r) for r in all_rules],
        )
