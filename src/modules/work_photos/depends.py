from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.handlers_files.depends import get_image_manager
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.depends import get_path_builder
from src.modules.path_builder.service import PathBuilder
from src.modules.work_photos.repository import WorkPhotoRepository
from src.modules.work_photos.service import WorkPhotoService


async def get_work_photo_repository(
    session: AsyncSession = Depends(get_db),
) -> WorkPhotoRepository:
    return WorkPhotoRepository(session=session)


async def get_work_photo_service(
    session: AsyncSession = Depends(get_db),
    repo: WorkPhotoRepository = Depends(get_work_photo_repository),
    image_manager: ImageManager = Depends(get_image_manager),
    path_builder: PathBuilder = Depends(get_path_builder),
) -> WorkPhotoService:
    return WorkPhotoService(
        repo=repo,
        session=session,
        image_manager=image_manager,
        path_builder=path_builder,
    )
