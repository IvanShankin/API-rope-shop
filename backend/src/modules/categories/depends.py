from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.handlers_files.depends import get_image_manager
from src.modules.handlers_files.service import ImageManager
from src.modules.path_builder.depends import get_path_builder
from src.modules.path_builder.service import PathBuilder
from src.modules.categories.repository import (
    CategoryRepository,
    CategoryTranslationRepository,
)
from src.modules.categories.service import CategoryService


def get_category_repository(
    session: AsyncSession = Depends(get_db),
) -> CategoryRepository:
    return CategoryRepository(session=session)


def get_category_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> CategoryTranslationRepository:
    return CategoryTranslationRepository(session=session)


def get_category_service(
    session: AsyncSession = Depends(get_db),
    category_repo: CategoryRepository = Depends(get_category_repository),
    translation_repo: CategoryTranslationRepository = Depends(get_category_translation_repository),
    image_manager: ImageManager = Depends(get_image_manager),
    path_builder: PathBuilder = Depends(get_path_builder),
) -> CategoryService:
    return CategoryService(
        category_repo=category_repo,
        translation_repo=translation_repo,
        session=session,
        image_manager=image_manager,
        path_builder=path_builder,
    )
