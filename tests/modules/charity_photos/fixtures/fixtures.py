import pytest_asyncio

from src.core.config import Config
from src.modules.charity_photos.models_dto import CharityPhotoResponseDTO
from tests.modules.charity_photos.fixtures.factory import (
    create_charity_photo_factory,
)
from tests.modules.charity_photos.fixtures.models_dto import (
    CreateCharityPhotoFixtureDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_charity_photo_fixture(not_open_session_db, config_fix: Config):
    async def _factory(
        new_photo: CreateCharityPhotoFixtureDTO = CreateCharityPhotoFixtureDTO(),
    ) -> CharityPhotoResponseDTO:
        async with not_open_session_db() as session:
            return await create_charity_photo_factory(
                session_db=session,
                new_photo=new_photo,
                config_fix=config_fix,
            )

    return _factory
