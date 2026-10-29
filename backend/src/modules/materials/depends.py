from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.materials.repository import (
    MaterialRepository,
    MaterialTranslationRepository,
)
from src.modules.materials.service import MaterialService


def get_material_repository(
    session: AsyncSession = Depends(get_db),
) -> MaterialRepository:
    return MaterialRepository(session=session)


def get_material_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> MaterialTranslationRepository:
    return MaterialTranslationRepository(session=session)


def get_material_service(
    material_repo: MaterialRepository = Depends(get_material_repository),
    translation_repo: MaterialTranslationRepository = Depends(get_material_translation_repository),
    session: AsyncSession = Depends(get_db),
) -> MaterialService:
    return MaterialService(
        material_repo=material_repo,
        translation_repo=translation_repo,
        session=session,
    )
