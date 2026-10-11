from typing import Callable, Awaitable, Optional
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.quote_requests.fixtures.models_dto import (
    CreateQuoteRequestFixtureDTO,
    CreateQuoteRopeItemFixtureDTO,
    CreateQuoteServiceItemFixtureDTO,
    CreateQuoteExtraItemFixtureDTO,
)
from tests.modules.quote_requests.fixtures.factory import (
    create_quote_request_factory,
    create_quote_rope_item_factory,
    create_quote_service_item_factory,
    create_quote_extra_item_factory,
)
from src.modules.quote_requests.models import QuoteRopeItem, QuoteServiceItem, QuoteExtraItem
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


@pytest_asyncio.fixture(scope="function")
async def create_quote_rope_item_fixture(
    session_db: AsyncSession,
) -> Callable[..., Awaitable[QuoteRopeItem]]:
    async def _factory(
        quote_request_id: Optional[int] = None,
        new_item: CreateQuoteRopeItemFixtureDTO = CreateQuoteRopeItemFixtureDTO(),
    ) -> QuoteRopeItem:
        return await create_quote_rope_item_factory(
            session_db=session_db,
            quote_request_id=quote_request_id,
            new_item=new_item,
        )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_quote_service_item_fixture(
    session_db: AsyncSession,
) -> Callable[..., Awaitable[QuoteServiceItem]]:
    async def _factory(
        quote_request_id: Optional[int] = None,
        new_item: CreateQuoteServiceItemFixtureDTO = CreateQuoteServiceItemFixtureDTO(),
    ) -> QuoteServiceItem:
        return await create_quote_service_item_factory(
            session_db=session_db,
            quote_request_id=quote_request_id,
            new_item=new_item,
        )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_quote_extra_item_fixture(
    session_db: AsyncSession,
) -> Callable[..., Awaitable[QuoteExtraItem]]:
    async def _factory(
        quote_request_id: Optional[int] = None,
        new_item: CreateQuoteExtraItemFixtureDTO = CreateQuoteExtraItemFixtureDTO(),
    ) -> QuoteExtraItem:
        return await create_quote_extra_item_factory(
            session_db=session_db,
            quote_request_id=quote_request_id,
            new_item=new_item,
        )

    return _factory
