import pytest_asyncio
from tests.modules.colors.fixtures.models_dto import (
    CreateColorFixtureDTO,
    CreateColorTranslationFixtureDTO,
)
from src.modules.colors.models_dto import (
    ColorResponseDTO,
    ColorTranslationResponseDTO,
)
from tests.modules.colors.fixtures.factory import (
    create_color_factory,
    create_color_translation_factory,
)


@pytest_asyncio.fixture(scope="function")
async def create_color_fixture(
    not_open_session_db
):
    async def _factory(
        new_color: CreateColorFixtureDTO = CreateColorFixtureDTO(),
    ) -> ColorResponseDTO:
        async with not_open_session_db() as session:
            return await create_color_factory(
                session_db=session,
                new_color=new_color,
            )
    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_color_translation_fixture(
    not_open_session_db
):
    async def _factory(
        new_trans: CreateColorTranslationFixtureDTO = CreateColorTranslationFixtureDTO(),
    ) -> ColorTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_color_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )
    return _factory
