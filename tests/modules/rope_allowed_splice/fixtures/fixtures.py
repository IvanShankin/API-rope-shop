from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO
from tests.modules.rope_allowed_splice.fixtures.factory import create_rope_allowed_splice_factory
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceResponseDTO


@pytest_asyncio.fixture(scope="function")
async def create_rope_allowed_splice_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateRopeAllowedSpliceFixtureDTO], Awaitable[RopeAllowedSpliceResponseDTO]]:
    async def _factory(
        new_item: CreateRopeAllowedSpliceFixtureDTO = CreateRopeAllowedSpliceFixtureDTO(),
    ) -> RopeAllowedSpliceResponseDTO:
        return await create_rope_allowed_splice_factory(
            session_db=session_db,
            new_item=new_item,
        )

    return _factory
