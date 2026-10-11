from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from tests.modules.rope_product_color.fixtures.factory import create_rope_product_color_factory
from src.modules.rope_product_color.models_dto import RopeProductColorResponseDTO


@pytest_asyncio.fixture(scope="function")
async def create_rope_product_color_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateRopeProductColorFixtureDTO], Awaitable[RopeProductColorResponseDTO]]:
    async def _factory(
        new_item: CreateRopeProductColorFixtureDTO = CreateRopeProductColorFixtureDTO(),
    ) -> RopeProductColorResponseDTO:
        return await create_rope_product_color_factory(
            session_db=session_db,
            new_item=new_item,
        )

    return _factory
