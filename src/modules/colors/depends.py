from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.colors.repository import ColorRepository, ColorTranslationRepository
from src.modules.colors.service import ColorService


def get_color_service(
    session: AsyncSession = Depends(get_db),
) -> ColorService:
    return ColorService(
        color_repo=ColorRepository(session=session),
        translation_repo=ColorTranslationRepository(session=session),
        session=session,
    )
