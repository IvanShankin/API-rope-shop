import pytest_asyncio
from tests.modules.splice_prices.fixtures.models_dto import CreateSplicePriceRuleFixtureDTO
from src.modules.splice_prices.models_dto import SplicePriceRuleResponseDTO
from tests.modules.splice_prices.fixtures.factory import create_splice_price_rule_factory

@pytest_asyncio.fixture(scope="function")
async def create_splice_price_rule_fixture(
    not_open_session_db
):
    async def _factory(
        new_rule: CreateSplicePriceRuleFixtureDTO = CreateSplicePriceRuleFixtureDTO(),
    ) -> SplicePriceRuleResponseDTO:
        async with not_open_session_db() as session:
            return await create_splice_price_rule_factory(
                session_db=session,
                new_rule=new_rule,
            )
    return _factory
