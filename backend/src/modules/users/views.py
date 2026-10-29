from fastapi import APIRouter, Depends
from starlette import status

from src.modules.auth.depends import get_current_user
from src.modules.users.depends import get_user_service
from src.modules.users.models_dto import (
    ChangePasswordDTO,
    ChangePasswordResponse,
    UserDTO,
    UserResponse,
)
from src.modules.users.service import UsersService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(user: UserDTO = Depends(get_current_user)):
    return user


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    data: ChangePasswordDTO,
    current_user: UserDTO = Depends(get_current_user),
    service: UsersService = Depends(get_user_service),
):
    """Смена пароля текущего пользователя."""
    await service.change_password(user_id=current_user.id, data=data)
    return ChangePasswordResponse()
