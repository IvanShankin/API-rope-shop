from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.auth.auth_service import AuthService
from src.modules.auth.depends import get_auth_service
from src.modules.content_blocks.repository import (
    ContentBlockRepository,
    ContentBlockTranslationRepository,
)
from src.modules.content_blocks.service import ContentBlockService
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


async def get_content_block_repository(
    session: AsyncSession = Depends(get_db),
) -> ContentBlockRepository:
    return ContentBlockRepository(session=session)


async def get_content_block_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> ContentBlockTranslationRepository:
    return ContentBlockTranslationRepository(session=session)


async def get_content_block_service(
    session: AsyncSession = Depends(get_db),
    block_repo: ContentBlockRepository = Depends(get_content_block_repository),
    trans_repo: ContentBlockTranslationRepository = Depends(
        get_content_block_translation_repository
    ),
) -> ContentBlockService:
    return ContentBlockService(
        block_repo=block_repo,
        trans_repo=trans_repo,
        session=session,
    )
