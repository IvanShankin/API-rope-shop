from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.splice_prices.repository import SplicePriceRuleRepository
from src.modules.splice_prices.models_dto import (
    SplicePriceRuleCreate,
    SplicePriceRuleUpdate,
    SplicePriceRuleResponseDTO,
    SplicePriceRuleWithRelationsResponseDTO
)
from src.modules.splice_prices.exception import SplicePriceRuleNotFound


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

    async def get_all_rules(self, is_active: Optional[bool] = None) -> List[SplicePriceRuleWithRelationsResponseDTO]:
        rules = await self.rule_repo.get_all(is_active=is_active)
        return [SplicePriceRuleWithRelationsResponseDTO.model_validate(r) for r in rules]

    async def get_rule_by_id(self, rule_id: int) -> SplicePriceRuleWithRelationsResponseDTO:
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise SplicePriceRuleNotFound(f"SplicePriceRule with id {rule_id} not found.")
        return SplicePriceRuleWithRelationsResponseDTO.model_validate(rule)
        
    async def get_rules_by_material_id(self, material_id: int) -> List[SplicePriceRuleWithRelationsResponseDTO]:
        rules = await self.rule_repo.get_by_splice_material_id(material_id)
        return [SplicePriceRuleWithRelationsResponseDTO.model_validate(r) for r in rules]
        
    async def get_rules_by_type_id(self, type_id: int) -> List[SplicePriceRuleWithRelationsResponseDTO]:
        rules = await self.rule_repo.get_by_splice_type_id(type_id)
        return [SplicePriceRuleWithRelationsResponseDTO.model_validate(r) for r in rules]

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
