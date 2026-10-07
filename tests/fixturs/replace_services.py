import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from helpers import test_crypto_context
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder import PathBuilder
from src.modules.splice_types.repository import (
    SpliceTypeRepository,
    SpliceTypeTranslationRepository,
)
from src.modules.splice_types.service import SpliceTypeService
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
async def image_manager_fixture(config_fix) -> ImageManager:
    return ImageManager(config=config_fix)


@pytest_asyncio.fixture(scope="function")
async def path_builder_fixture(config_fix) -> PathBuilder:
    return PathBuilder(config=config_fix)


@pytest_asyncio.fixture(scope="function")
async def splice_type_service_fixture(
    session_db: AsyncSession,
    image_manager_fixture: ImageManager,
    path_builder_fixture: PathBuilder,
) -> SpliceTypeService:
    return SpliceTypeService(
        type_repo=SpliceTypeRepository(session=session_db),
        translation_repo=SpliceTypeTranslationRepository(session=session_db),
        session=session_db,
        image_manager=image_manager_fixture,
        path_builder=path_builder_fixture,
    )
