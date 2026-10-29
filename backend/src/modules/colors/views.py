from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import (
    get_current_admin,
    get_optional_admin,
)
from src.modules.users.models_dto import UserDTO
from src.modules.colors.models_dto import (
    ColorResponseDTO,
    ColorLocalizedResponseDTO,
    ColorCreate,
    ColorUpdate,
    ColorUpdateIndexDTO,
    ColorTranslationResponseDTO,
    ColorTranslationCreate,
    ColorTranslationUpdate,
)
from src.modules.colors.service import ColorService
from src.modules.colors.depends import get_color_service

router = APIRouter(prefix="/colors", tags=["Colors"])


@router.get("", response_model=List[ColorLocalizedResponseDTO], status_code=status.HTTP_200_OK)
async def get_all_colors(
    locale: Optional[Language] = Query(None, description="Language for translation"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (admin only)"),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: ColorService = Depends(get_color_service),
):
    """Get all colors (public, admin only for inactive)."""
    return await service.get_all_colors(locale=locale, is_active=is_active, is_admin=admin is not None)


@router.get("/{color_id}", response_model=ColorResponseDTO, status_code=status.HTTP_200_OK)
async def get_color(
    color_id: int,
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: ColorService = Depends(get_color_service),
):
    """Get color by ID with all translations (public, admin only for inactive)."""
    return await service.get_color_by_id(color_id, is_admin=admin is not None)


@router.post("", response_model=ColorResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_color(
    data: ColorCreate,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new color (admin only)."""
    return await service.create_color(data)


@router.patch("/{color_id}", response_model=ColorResponseDTO, status_code=status.HTTP_200_OK)
async def update_color(
    color_id: int,
    data: ColorUpdate,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update a color attributes (code, hex, is_active) (admin only)."""
    return await service.update_color(color_id, data)


@router.patch("/{color_id}/index", response_model=ColorResponseDTO, status_code=status.HTTP_200_OK)
async def update_color_index(
    color_id: int,
    data: ColorUpdateIndexDTO,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update color order index with automatic neighbor shifting (admin only)."""
    return await service.reorder_color(color_id, data)


@router.delete("/{color_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_color(
    color_id: int,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete a color (admin only)."""
    await service.delete_color(color_id)


@router.post("/{color_id}/translations", response_model=ColorTranslationResponseDTO, status_code=status.HTTP_201_CREATED)
async def add_translation(
    color_id: int,
    data: ColorTranslationCreate,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Add a translation for a color (admin only)."""
    return await service.create_translation(color_id, data)


@router.patch("/translations/{translation_id}", response_model=ColorTranslationResponseDTO, status_code=status.HTTP_200_OK)
async def update_translation(
    translation_id: int,
    data: ColorTranslationUpdate,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update a translation (admin only)."""
    return await service.update_translation(translation_id, data)


@router.delete("/translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_translation(
    translation_id: int,
    service: ColorService = Depends(get_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete a translation (admin only)."""
    await service.delete_translation(translation_id)
