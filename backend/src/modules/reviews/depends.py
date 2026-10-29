from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.auth.auth_service import AuthService
from src.modules.auth.depends import get_auth_service
from src.modules.reviews.repository import (
    ReviewRepository,
    ReviewTranslationRepository,
)
from src.modules.reviews.service import ReviewService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserDTO

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False,
)


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[UserDTO]:
    """Извлекает пользователя из токена, если он передан; возвращает None для гостя."""
    if not token:
        return None
    try:
        return await auth_service.get_current_user(token)
    except Exception:
        return None


async def get_optional_admin(
    user: Optional[UserDTO] = Depends(get_optional_current_user),
) -> Optional[UserDTO]:
    """Возвращает UserDTO, только если пользователь авторизован и является ADMIN."""
    if user and user.role == UserRole.ADMIN:
        return user
    return None


async def get_review_repository(
    session: AsyncSession = Depends(get_db),
) -> ReviewRepository:
    return ReviewRepository(session=session)


async def get_review_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> ReviewTranslationRepository:
    return ReviewTranslationRepository(session=session)


async def get_review_service(
    session: AsyncSession = Depends(get_db),
    review_repo: ReviewRepository = Depends(get_review_repository),
    translation_repo: ReviewTranslationRepository = Depends(
        get_review_translation_repository
    ),
) -> ReviewService:
    return ReviewService(
        review_repo=review_repo,
        translation_repo=translation_repo,
        session=session,
    )
