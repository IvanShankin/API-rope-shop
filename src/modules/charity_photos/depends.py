from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.handlers_files.depends import get_image_manager
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.depends import get_path_builder
from src.modules.path_builder.service import PathBuilder
from src.modules.charity_photos.repository import (
    CharityPhotoRepository,
    CharityPhotoTranslationRepository,
)
from src.modules.charity_photos.service import CharityPhotoService


async def get_charity_photo_repository(
    session: AsyncSession = Depends(get_db),
) -> CharityPhotoRepository:
    return CharityPhotoRepository(session=session)


async def get_charity_photo_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> CharityPhotoTranslationRepository:
    return CharityPhotoTranslationRepository(session=session)


async def get_charity_photo_service(
    session: AsyncSession = Depends(get_db),
    repo: CharityPhotoRepository = Depends(get_charity_photo_repository),
    translation_repo: CharityPhotoTranslationRepository = Depends(get_charity_photo_translation_repository),
    image_manager: ImageManager = Depends(get_image_manager),
    path_builder: PathBuilder = Depends(get_path_builder),
) -> CharityPhotoService:
    return CharityPhotoService(
        repo=repo,
        translation_repo=translation_repo,
        session=session,
        image_manager=image_manager,
        path_builder=path_builder,
    )
