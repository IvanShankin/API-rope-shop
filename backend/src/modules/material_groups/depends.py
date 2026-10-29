from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.material_groups.repository import (
    MaterialGroupRepository,
    MaterialGroupTranslationRepository,
)
from src.modules.material_groups.service import MaterialGroupService


def get_material_group_repository(
    session: AsyncSession = Depends(get_db)
) -> MaterialGroupRepository:
    return MaterialGroupRepository(session=session)


def get_material_group_translation_repository(
    session: AsyncSession = Depends(get_db)
) -> MaterialGroupTranslationRepository:
    return MaterialGroupTranslationRepository(session=session)


def get_material_group_service(
    session: AsyncSession = Depends(get_db),
    group_repo: MaterialGroupRepository = Depends(get_material_group_repository),
    translation_repo: MaterialGroupTranslationRepository = Depends(get_material_group_translation_repository),
) -> MaterialGroupService:
    return MaterialGroupService(
        group_repo=group_repo,
        translation_repo=translation_repo,
        session=session,
    )
