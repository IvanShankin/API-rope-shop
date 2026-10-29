import pytest_asyncio

from src.core.config import Config
from src.modules.work_photos.models_dto import WorkPhotoResponseDTO
from tests.modules.work_photos.fixtures.factory import create_work_photo_factory
from tests.modules.work_photos.fixtures.models_dto import (
    CreateWorkPhotoFixtureDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_work_photo_fixture(not_open_session_db, config_fix: Config,):
    async def _factory(
        new_photo: CreateWorkPhotoFixtureDTO = CreateWorkPhotoFixtureDTO(),
    ) -> WorkPhotoResponseDTO:
        async with not_open_session_db() as session:
            return await create_work_photo_factory(
                session_db=session,
                new_photo=new_photo,
                config_fix=config_fix,
            )

    return _factory
