import pytest_asyncio
from tests.modules.categories.fixtures.models_dto import (
    CreateCategoryFixtureDTO,
    CreateCategoryTranslationFixtureDTO,
)
from src.modules.categories.models_dto import (
    CategoryResponseDTO,
    CategoryTranslationResponseDTO,
)
from tests.modules.categories.fixtures.factory import (
    create_category_factory,
    create_category_translation_factory,
)


@pytest_asyncio.fixture(scope="function")
async def create_category_fixture(
    not_open_session_db
):
    async def _factory(
        new_category: CreateCategoryFixtureDTO = CreateCategoryFixtureDTO(),
    ) -> CategoryResponseDTO:
        async with not_open_session_db() as session:
            return await create_category_factory(
                session_db=session,
                new_category=new_category,
            )
    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_category_translation_fixture(
    not_open_session_db
):
    async def _factory(
        new_trans: CreateCategoryTranslationFixtureDTO = CreateCategoryTranslationFixtureDTO(),
    ) -> CategoryTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_category_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )
    return _factory
