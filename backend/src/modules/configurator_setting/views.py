from fastapi import APIRouter, Depends
from starlette import status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.configurator_setting.models_dto import (
    ConfiguratorSettingResponseDTO,
    ConfiguratorSettingUpdateDTO,
)
from src.modules.configurator_setting.service import ConfiguratorSettingService
from src.modules.configurator_setting.depends import get_configurator_setting_service

router = APIRouter(prefix="/configurator_settings", tags=["Configurator Settings"])


@router.get(
    "",
    response_model=ConfiguratorSettingResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_configurator_settings(
    service: ConfiguratorSettingService = Depends(get_configurator_setting_service),
):
    """Get current configurator settings."""
    return await service.get_settings()


@router.patch(
    "",
    response_model=ConfiguratorSettingResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_configurator_settings(
    data: ConfiguratorSettingUpdateDTO,
    service: ConfiguratorSettingService = Depends(get_configurator_setting_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update configurator settings (admin only)."""
    return await service.update_settings(data=data)
