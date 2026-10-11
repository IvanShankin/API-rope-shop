from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.configurator_extra.models import BillingType
from src.modules.configurator_extra.models_dto import (
    ConfiguratorExtraCreate,
    ConfiguratorExtraUpdate,
    ConfiguratorExtraUpdateIndexDTO,
    ConfiguratorExtraResponseDTO,
    ConfiguratorExtraLocalizedResponseDTO,
    ConfiguratorExtraTranslationCreate,
    ConfiguratorExtraTranslationUpdate,
    ConfiguratorExtraTranslationResponseDTO,
)
from src.modules.configurator_extra.service import ConfiguratorExtraService
from src.modules.configurator_extra.depends import get_configurator_extra_service

router = APIRouter(prefix="/configurator_extras", tags=["Configurator Extras"])


@router.get(
    "",
    response_model=List[ConfiguratorExtraLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_all_configurator_extras(
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    billing_type: Optional[BillingType] = Query(None, description="Filter by billing type"),
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
):
    """Get all configurator extra options with localized names (public)."""
    return await service.get_all_extras(
        locale=locale,
        is_active=is_active,
        billing_type=billing_type,
    )


@router.get(
    "/{id}",
    response_model=ConfiguratorExtraResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_configurator_extra(
    id: int,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
):
    """Get configurator extra option by ID with all translations (public)."""
    return await service.get_extra_by_id(extra_id=id)


@router.post(
    "",
    response_model=ConfiguratorExtraResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_configurator_extra(
    data: ConfiguratorExtraCreate,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new configurator extra option with translations (admin only)."""
    return await service.create_extra(data=data)


@router.patch(
    "/{id}",
    response_model=ConfiguratorExtraResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_configurator_extra(
    id: int,
    data: ConfiguratorExtraUpdate,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update configurator extra option properties (admin only)."""
    return await service.update_extra(extra_id=id, data=data)


@router.patch(
    "/{id}/index",
    response_model=ConfiguratorExtraResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def reorder_configurator_extra(
    id: int,
    data: ConfiguratorExtraUpdateIndexDTO,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Reorder configurator extra option position (admin only)."""
    return await service.reorder_extra(extra_id=id, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_configurator_extra(
    id: int,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete configurator extra option (admin only)."""
    await service.delete_extra(extra_id=id)


# ==================== Translations Endpoints ====================

@router.post(
    "/{id}/translations",
    response_model=ConfiguratorExtraTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def add_translation(
    id: int,
    data: ConfiguratorExtraTranslationCreate,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Add a translation for a configurator extra option (admin only)."""
    return await service.create_translation(extra_id=id, data=data)


@router.patch(
    "/translations/{translation_id}",
    response_model=ConfiguratorExtraTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_translation(
    translation_id: int,
    data: ConfiguratorExtraTranslationUpdate,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update an existing translation (admin only)."""
    return await service.update_translation(translation_id=translation_id, data=data)


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_translation(
    translation_id: int,
    service: ConfiguratorExtraService = Depends(get_configurator_extra_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete a translation (admin only, forbidden to delete the last remaining translation)."""
    await service.delete_translation(translation_id=translation_id)
