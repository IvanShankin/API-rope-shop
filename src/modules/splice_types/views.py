from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin, get_optional_admin
from src.modules.users.models_dto import UserDTO
from src.modules.splice_types.models import SpliceCategory
from src.modules.splice_types.models_dto import (
    SpliceTypeResponseDTO,
    SpliceTypeLocalizedResponseDTO,
    SpliceTypeCreate,
    SpliceTypeUpdate,
    SpliceTypeTranslationResponseDTO,
    SpliceTypeTranslationCreate,
    SpliceTypeTranslationUpdate
)
from src.modules.splice_types.service import SpliceTypeService
from src.modules.splice_types.depends import get_splice_type_service

router = APIRouter(prefix="/splice_types", tags=["Splice Types"])


@router.get("", response_model=List[SpliceTypeLocalizedResponseDTO], status_code=status.HTTP_200_OK)
async def get_all_splice_types(
    locale: Optional[Language] = Query(None, description="Language for translation"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    category: Optional[SpliceCategory] = Query(None, description="Filter by category (loop, splice)"),
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
):
    """Get all splice types (public)."""
    effective_active = is_active if admin is not None else True
    if category:
        return await service.get_splice_types_by_category(category=category, locale=locale, is_active=effective_active)
    return await service.get_all_splice_types(locale=locale, is_active=effective_active)


@router.get(
    "/{type_id}",
    response_model=SpliceTypeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get splice type by ID",
    description="Get splice type details with all translations (admin only).",
)
async def get_splice_type_by_id(
    type_id: int,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin),
) -> SpliceTypeResponseDTO:
    """Get splice type details with all translations (admin only)."""
    return await service.get_splice_type_by_id(type_id=type_id)


@router.post("", response_model=SpliceTypeResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_splice_type(
    data: SpliceTypeCreate,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Create a new splice type (admin only)."""
    return await service.create_splice_type(data)


@router.patch("/{type_id}", response_model=SpliceTypeResponseDTO, status_code=status.HTTP_200_OK)
async def update_splice_type(
    type_id: int,
    data: SpliceTypeUpdate,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Update a splice type (admin only)."""
    return await service.update_splice_type(type_id, data)


@router.post("/{type_id}/image", response_model=SpliceTypeResponseDTO, status_code=status.HTTP_200_OK)
async def upload_splice_type_image(
    type_id: int,
    file: UploadFile = File(..., description="Image file (jpg, png, heic, webp, etc.)"),
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Upload and convert image for a splice type (admin only)."""
    return await service.upload_image(type_id=type_id, file=file)


@router.delete("/{type_id}/image", response_model=SpliceTypeResponseDTO, status_code=status.HTTP_200_OK)
async def delete_splice_type_image(
    type_id: int,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Delete image of a splice type (admin only)."""
    return await service.delete_image(type_id=type_id)


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_splice_type(
    type_id: int,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Delete a splice type (admin only)."""
    await service.delete_splice_type(type_id)


@router.post("/{type_id}/translations", response_model=SpliceTypeTranslationResponseDTO, status_code=status.HTTP_201_CREATED)
async def add_translation(
    type_id: int,
    data: SpliceTypeTranslationCreate,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Add a translation for a splice type (admin only)."""
    return await service.create_translation(type_id, data)


@router.patch("/translations/{translation_id}", response_model=SpliceTypeTranslationResponseDTO, status_code=status.HTTP_200_OK)
async def update_translation(
    translation_id: int,
    data: SpliceTypeTranslationUpdate,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Update a translation (admin only)."""
    return await service.update_translation(translation_id, data)


@router.delete("/translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_translation(
    translation_id: int,
    service: SpliceTypeService = Depends(get_splice_type_service),
    admin: UserDTO = Depends(get_current_admin)
):
    """Delete a translation (admin only)."""
    await service.delete_translation(translation_id)
