from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.quote_requests.fixtures.models_dto import CreateQuoteRequestFixtureDTO
from tests.modules.quote_requests.fixtures.factory import create_quote_request_factory
from src.modules.quote_requests.models_dto import QuoteRequestResponseDTO


@pytest_asyncio.fixture(scope="function")
async def create_quote_request_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateQuoteRequestFixtureDTO], Awaitable[QuoteRequestResponseDTO]]:
    async def _factory(
        new_request: CreateQuoteRequestFixtureDTO = CreateQuoteRequestFixtureDTO(),
    ) -> QuoteRequestResponseDTO:
        return await create_quote_request_factory(
            session_db=session_db,
            new_request=new_request,
        )

    return _factory
