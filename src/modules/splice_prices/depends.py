from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.splice_prices.repository import SplicePriceRuleRepository
from src.modules.splice_prices.service import SplicePriceRuleService


def get_splice_price_service(
    session: AsyncSession = Depends(get_db),
) -> SplicePriceRuleService:
    return SplicePriceRuleService(
        rule_repo=SplicePriceRuleRepository(session=session),
        session=session
    )
