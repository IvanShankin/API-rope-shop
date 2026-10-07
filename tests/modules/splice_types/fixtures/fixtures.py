import pytest_asyncio
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from src.modules.splice_types.models_dto import SpliceTypeResponseDTO
from tests.modules.splice_types.fixtures.factory import create_splice_type_factory

@pytest_asyncio.fixture(scope="function")
async def create_splice_type_fixture(
    not_open_session_db
):
    async def _factory(
        new_type: CreateSpliceTypeFixtureDTO = CreateSpliceTypeFixtureDTO(),
    ) -> SpliceTypeResponseDTO:
        async with not_open_session_db() as session:
            return await create_splice_type_factory(
                session_db=session,
                new_type=new_type,
            )
    return _factory
