from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin, get_optional_admin
from src.modules.users.models_dto import UserDTO
from src.modules.rope_allowed_splice.models_dto import (
    RopeAllowedSpliceResponseDTO,
    RopeAllowedSpliceLocalizedResponseDTO,
    RopeAllowedSpliceCreate,
    RopeAllowedSpliceBulkSetDTO,
)
from src.modules.rope_allowed_splice.service import RopeAllowedSpliceService
from src.modules.rope_allowed_splice.depends import get_rope_allowed_splice_service

router = APIRouter(prefix="/rope_allowed_splices", tags=["Rope Allowed Splices"])


@router.get(
    "/by-product/{product_id}",
    response_model=List[RopeAllowedSpliceLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_allowed_splices_by_product(
    product_id: int,
    locale: Optional[Language] = Query(None, description="Language for splice type localization"),
    service: RopeAllowedSpliceService = Depends(get_rope_allowed_splice_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
):
    """Get all allowed splice types of a specific product (public)."""
    return await service.get_allowed_splices_by_product_id(
        product_id=product_id,
        locale=locale,
        is_admin=admin is not None,
    )


@router.get(
    "/{product_id}/{splice_type_id}",
    response_model=RopeAllowedSpliceResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_rope_allowed_splice(
    product_id: int,
    splice_type_id: int,
    service: RopeAllowedSpliceService = Depends(get_rope_allowed_splice_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
):
    """Get rope allowed splice link by composite key (public)."""
    return await service.get_by_composite_key(
        product_id=product_id,
        splice_type_id=splice_type_id,
        is_admin=admin is not None,
    )


@router.post(
    "",
    response_model=RopeAllowedSpliceResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_rope_allowed_splice(
    data: RopeAllowedSpliceCreate,
    service: RopeAllowedSpliceService = Depends(get_rope_allowed_splice_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Link a splice type to a product (admin only)."""
    return await service.create_rope_allowed_splice(data=data)


@router.put(
    "/by-product/{product_id}",
    response_model=List[RopeAllowedSpliceResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def set_allowed_splices_for_product(
    product_id: int,
    data: RopeAllowedSpliceBulkSetDTO,
    service: RopeAllowedSpliceService = Depends(get_rope_allowed_splice_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Bulk set/overwrite allowed splice types for a product (admin only)."""
    return await service.set_allowed_splices_for_product(
        product_id=product_id,
        data=data,
    )


@router.delete(
    "/{product_id}/{splice_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rope_allowed_splice(
    product_id: int,
    splice_type_id: int,
    service: RopeAllowedSpliceService = Depends(get_rope_allowed_splice_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Unlink a splice type from a product (admin only)."""
    await service.delete_rope_allowed_splice(
        product_id=product_id,
        splice_type_id=splice_type_id,
    )
