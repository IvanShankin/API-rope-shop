import pytest_asyncio
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from src.modules.splice_types.models_dto import (
    SpliceTypeResponseDTO,
    SpliceTypeTranslationResponseDTO,
)
from tests.modules.splice_types.fixtures.factory import (
    create_splice_type_factory,
    create_splice_type_translation_factory,
)


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


@pytest_asyncio.fixture(scope="function")
async def create_splice_type_translation_fixture(
    not_open_session_db
):
    async def _factory(
        new_trans: CreateSpliceTypeTranslationFixtureDTO = CreateSpliceTypeTranslationFixtureDTO(),
    ) -> SpliceTypeTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_splice_type_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )
    return _factory
