from fastapi import Depends

from src.modules.auth.depends import get_current_user
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserDTO


async def get_current_admin(
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, является ли пользователь админом.
    :raises PermissionErrorService:
    """
    if current_user.role == UserRole.ADMIN:
        raise PermissionErrorService()
    return current_user
