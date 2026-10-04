import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from helpers import test_crypto_context
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService


@pytest_asyncio.fixture(scope="function")
async def user_service_fixture(session_db: AsyncSession, config_fix) -> UsersService:
    return UsersService(
        users_repo=UsersRepository(session=session_db),
        cr_context=test_crypto_context,
        session_db=session_db,
    )


@pytest_asyncio.fixture(scope="function")
async def compression_images_fixture(config_fix) -> CompressionImages:
    return CompressionImages(config=config_fix)


@pytest_asyncio.fixture(scope="function")
async def handler_images_fixture(config_fix) -> HandlerImages:
    return HandlerImages(config=config_fix)


@pytest_asyncio.fixture(scope="function")
async def path_builder_fixture(config_fix) -> PathBuilder:
    return PathBuilder(config=config_fix)

