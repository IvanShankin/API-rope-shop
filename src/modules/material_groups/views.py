from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.material_groups.models_dto import (
    MaterialGroupCreate,
    MaterialGroupUpdate,
    MaterialGroupUpdateIndexDTO,
    MaterialGroupResponseDTO,
    MaterialGroupLocalizedResponseDTO,
    MaterialGroupTranslationCreate,
    MaterialGroupTranslationUpdate,
    MaterialGroupTranslationResponseDTO,
)
from src.modules.material_groups.service import MaterialGroupService
from src.modules.material_groups.depends import get_material_group_service

router = APIRouter(prefix="/material_groups", tags=["Material Groups"])


@router.get(
    "",
    response_model=List[MaterialGroupLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_all_material_groups(
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: MaterialGroupService = Depends(get_material_group_service),
):
    """Get all material groups with localized names (public)."""
    return await service.get_all_material_groups(locale=locale, is_active=is_active)


@router.get(
    "/{id}",
    response_model=MaterialGroupResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_material_group(
    id: int,
    service: MaterialGroupService = Depends(get_material_group_service),
):
    """Get material group by ID with all translations (public)."""
    return await service.get_material_group_by_id(group_id=id)


@router.post(
    "",
    response_model=MaterialGroupResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_material_group(
    data: MaterialGroupCreate,
    service: MaterialGroupService = Depends(get_material_group_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new material group with translations (admin only)."""
    return await service.create_material_group(data=data)


@router.patch(
    "/{id}",
    response_model=MaterialGroupResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_material_group(
    id: int,
    data: MaterialGroupUpdate,
    service: MaterialGroupService = Depends(get_material_group_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update material group properties (admin only)."""
    return await service.update_material_group(group_id=id, data=data)


@router.patch(
    "/{id}/index",
    response_model=MaterialGroupResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def reorder_material_group(
    id: int,
    data: MaterialGroupUpdateIndexDTO,
    service: MaterialGroupService = Depends(get_material_group_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Reorder material group position with neighbors shift (admin only)."""
    return await service.reorder_material_group(group_id=id, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material_group(
    id: int,
    service: MaterialGroupService = Depends(get_material_group_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete material group (admin only, forbidden if dependent materials or rope products exist)."""
    await service.delete_material_group(group_id=id)


# ==================== Translations Endpoints ====================

@router.post(
    "/{id}/translations",
    response_model=MaterialGroupTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def add_translation(
    id: int,
    data: MaterialGroupTranslationCreate,
    service: MaterialGroupService = Depends(get_material_group_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Add a translation for a material group (admin only)."""
    return await service.create_translation(group_id=id, data=data)


@router.patch(
    "/translations/{translation_id}",
    response_model=MaterialGroupTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_translation(
    translation_id: int,
    data: MaterialGroupTranslationUpdate,
    service: MaterialGroupService = Depends(get_material_group_service),
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
    service: MaterialGroupService = Depends(get_material_group_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete a translation (admin only, forbidden to delete the last translation)."""
    await service.delete_translation(translation_id=translation_id)
