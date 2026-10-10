from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.rope_products.fixtures.models_dto import CreateRopeProductFixtureDTO
from tests.modules.rope_products.fixtures.factory import create_rope_product_factory
from src.modules.rope_products.models import RopeProduct


@pytest_asyncio.fixture(scope="function")
async def create_rope_product_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateRopeProductFixtureDTO], Awaitable[RopeProduct]]:
    async def _factory(
        new_product: CreateRopeProductFixtureDTO = CreateRopeProductFixtureDTO(),
    ) -> RopeProduct:
        return await create_rope_product_factory(
            session_db=session_db,
            new_product=new_product,
        )

    return _factory
