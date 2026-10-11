import random
from sqlalchemy.ext.asyncio import AsyncSession
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.splice_prices.models_dto import SplicePriceRuleResponseDTO
from tests.modules.splice_types.fixtures.factory import create_splice_type_factory
from tests.modules.splice_materials.fixtures.factory import create_splice_material_factory

async def create_splice_price_rule_factory(
    session_db: AsyncSession,
    new_rule: CreateSplicePriceRuleFixtureDTO = CreateSplicePriceRuleFixtureDTO()
) -> SplicePriceRuleResponseDTO:
    splice_type_id = new_rule.splice_type_id
    if splice_type_id is None:
        st = await create_splice_type_factory(session_db=session_db)
        splice_type_id = st.id
        
    splice_material_id = new_rule.splice_material_id
    if splice_material_id is None:
        sm = await create_splice_material_factory(session_db=session_db)
        splice_material_id = sm.id

    rule = SplicePriceRule(
        splice_type_id=splice_type_id,
        splice_material_id=splice_material_id,
        diameter_from_mm=10.0 if new_rule.diameter_from_mm is None else new_rule.diameter_from_mm,
        diameter_to_mm=20.0 if new_rule.diameter_to_mm is None else new_rule.diameter_to_mm,
        price=100.50 if new_rule.price is None else new_rule.price,
        is_active=True if new_rule.is_active is None else new_rule.is_active,
    )
    session_db.add(rule)
    await session_db.commit()
    await session_db.refresh(rule)
    
    return SplicePriceRuleResponseDTO.model_validate(rule)
