from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import (
    get_current_admin,
    get_optional_admin,
)
from src.modules.users.models_dto import UserDTO
from src.modules.materials.models_dto import (
    MaterialCreate,
    MaterialUpdate,
    MaterialUpdateIndexDTO,
    MaterialResponseDTO,
    MaterialLocalizedResponseDTO,
    MaterialTranslationCreate,
    MaterialTranslationUpdate,
    MaterialTranslationResponseDTO,
)
from src.modules.materials.service import MaterialService
from src.modules.materials.depends import get_material_service

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.get(
    "",
    response_model=List[MaterialLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_all_materials(
    material_group_id: Optional[int] = Query(None, description="Filter by material group ID"),
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (admin only)"),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: MaterialService = Depends(get_material_service),
):
    """Get all materials with localized names (public, admin only for inactive)."""
    return await service.get_all_materials(
        material_group_id=material_group_id,
        locale=locale,
        is_active=is_active,
        is_admin=admin is not None,
    )


@router.get(
    "/{id}",
    response_model=MaterialResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_material(
    id: int,
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: MaterialService = Depends(get_material_service),
):
    """Get material by ID with all translations (public, admin only for inactive)."""
    return await service.get_material_by_id(material_id=id, is_admin=admin is not None)


@router.post(
    "",
    response_model=MaterialResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_material(
    data: MaterialCreate,
    service: MaterialService = Depends(get_material_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new material with translations (admin only)."""
    return await service.create_material(data=data)


@router.patch(
    "/{id}",
    response_model=MaterialResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_material(
    id: int,
    data: MaterialUpdate,
    service: MaterialService = Depends(get_material_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update material properties (admin only)."""
    return await service.update_material(material_id=id, data=data)


@router.patch(
    "/{id}/index",
    response_model=MaterialResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def reorder_material(
    id: int,
    data: MaterialUpdateIndexDTO,
    service: MaterialService = Depends(get_material_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Reorder material position within its material group (admin only)."""
    return await service.reorder_material(material_id=id, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_material(
    id: int,
    service: MaterialService = Depends(get_material_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete material (admin only, forbidden if dependent entities exist)."""
    await service.delete_material(material_id=id)


# ==================== Translations Endpoints ====================

@router.post(
    "/{id}/translations",
    response_model=MaterialTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def add_translation(
    id: int,
    data: MaterialTranslationCreate,
    service: MaterialService = Depends(get_material_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Add a translation for a material (admin only)."""
    return await service.create_translation(material_id=id, data=data)


@router.patch(
    "/translations/{translation_id}",
    response_model=MaterialTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_translation(
    translation_id: int,
    data: MaterialTranslationUpdate,
    service: MaterialService = Depends(get_material_service),
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
    service: MaterialService = Depends(get_material_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete a translation (admin only, forbidden to delete the last translation)."""
    await service.delete_translation(translation_id=translation_id)
