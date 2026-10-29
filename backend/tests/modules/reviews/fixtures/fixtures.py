import pytest_asyncio

from src.modules.reviews.models_dto import (
    ReviewResponseDTO,
    ReviewTranslationResponseDTO,
)
from tests.modules.reviews.fixtures.factory import (
    create_review_factory,
    create_review_translation_factory,
)
from tests.modules.reviews.fixtures.models_dto import (
    CreateReviewFixtureDTO,
    CreateReviewTranslationFixtureDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_review_fixture(not_open_session_db):
    async def _factory(
        new_review: CreateReviewFixtureDTO = CreateReviewFixtureDTO(),
    ) -> ReviewResponseDTO:
        async with not_open_session_db() as session:
            return await create_review_factory(
                session_db=session,
                new_review=new_review,
            )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_review_translation_fixture(not_open_session_db):
    async def _factory(
        new_trans: CreateReviewTranslationFixtureDTO = CreateReviewTranslationFixtureDTO(),
    ) -> ReviewTranslationResponseDTO:
        async with not_open_session_db() as session:
            return await create_review_translation_factory(
                session_db=session,
                new_trans=new_trans,
            )

    return _factory
