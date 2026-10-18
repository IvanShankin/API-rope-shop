import pytest_asyncio

from src.modules.content_blocks.models_dto import (
    ContentBlockResponseDTO,
    ContentBlockTranslationResponseDTO,
)
from tests.modules.content_blocks.fixtures.factory import (
    create_content_block_factory,
    create_content_block_translation_factory,
)
from tests.modules.content_blocks.fixtures.models_dto import (
    CreateContentBlockFixtureDTO,
    CreateContentBlockTranslationFixtureDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_content_block_fixture(not_open_session_db):
    async def _factory(
        new_block: CreateContentBlockFixtureDTO = CreateContentBlockFixtureDTO(),
    ) -> ContentBlockResponseDTO:
        async with not_open_session_db() as session:
            return await create_content_block_factory(
                session_db=session,
                new_block=new_block,
            )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_content_block_translation_fixture(not_open_session_db):
    async def _factory(
        new_trans: CreateContentBlockTranslationFixtureDTO = CreateContentBlockTranslationFixtureDTO(),
    ) -> ContentBlockTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_content_block_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )

    return _factory
