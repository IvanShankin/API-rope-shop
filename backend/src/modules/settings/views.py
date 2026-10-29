from fastapi import APIRouter, Depends
from starlette import status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.settings.models_dto import (
    SettingsResponseDTO,
    SettingsUpdateDTO, SettingsPublicResponseDTO,
)
from src.modules.settings.service import SettingsService
from src.modules.settings.depends import get_settings_service

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get(
    "/public",
    response_model=SettingsPublicResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get public settings",
    description="Get public site settings (public access, no credentials exposed).",
)
async def get_public_settings(
    service: SettingsService = Depends(get_settings_service),
) -> SettingsPublicResponseDTO:
    """Получение публичных настроек сайта (публичный доступ)."""
    return await service.get_public_settings()


@router.get(
    "",
    response_model=SettingsResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_settings(
    service: SettingsService = Depends(get_settings_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Получение системных настроек (только для администратора)."""
    return await service.get_settings()


@router.patch(
    "",
    response_model=SettingsResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def patch_settings(
    data: SettingsUpdateDTO,
    service: SettingsService = Depends(get_settings_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Частичное обновление системных настроек (только для администратора)."""
    return await service.update_settings(data=data)


@router.put(
    "",
    response_model=SettingsResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def put_settings(
    data: SettingsUpdateDTO,
    service: SettingsService = Depends(get_settings_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Полное/частичное обновление системных настроек (только для администратора)."""
    return await service.update_settings(data=data)
