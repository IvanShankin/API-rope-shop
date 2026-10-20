from typing import Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from src.modules.auth.auth_service import AuthService
from src.modules.auth.depends import get_auth_service, get_current_user
from src.modules.check_permission.exception import PermissionErrorService
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


async def get_current_admin(
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, является ли пользователь админом.
    :raises PermissionErrorService:
    """
    if current_user.role != UserRole.ADMIN:
        raise PermissionErrorService()
    return current_user

