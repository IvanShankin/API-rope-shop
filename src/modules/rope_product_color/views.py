from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.rope_product_color.models_dto import (
    RopeProductColorResponseDTO,
    RopeProductColorLocalizedResponseDTO,
    RopeProductColorCreate,
    RopeProductColorUpdateIndexDTO,
)
from src.modules.rope_product_color.service import RopeProductColorService
from src.modules.rope_product_color.depends import get_rope_product_color_service

router = APIRouter(prefix="/rope_product_colors", tags=["Rope Product Colors"])


@router.get(
    "/by-product/{rope_product_id}",
    response_model=List[RopeProductColorLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_colors_by_product(
    rope_product_id: int,
    locale: Optional[Language] = Query(None, description="Language for color name localization"),
    service: RopeProductColorService = Depends(get_rope_product_color_service),
):
    """Get all colors of a specific rope product (public)."""
    return await service.get_colors_by_product_id(
        rope_product_id=rope_product_id,
        locale=locale,
    )


@router.get(
    "/{id}",
    response_model=RopeProductColorResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_rope_product_color(
    id: int,
    service: RopeProductColorService = Depends(get_rope_product_color_service),
):
    """Get rope product color link by ID (public)."""
    return await service.get_by_id(item_id=id)


@router.post(
    "",
    response_model=RopeProductColorResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_rope_product_color(
    data: RopeProductColorCreate,
    service: RopeProductColorService = Depends(get_rope_product_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Link a color to a rope product (admin only)."""
    return await service.create_rope_product_color(data=data)


@router.patch(
    "/{id}/index",
    response_model=RopeProductColorResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_rope_product_color_index(
    id: int,
    data: RopeProductColorUpdateIndexDTO,
    service: RopeProductColorService = Depends(get_rope_product_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update display order index of a color within a rope product (admin only)."""
    return await service.reorder_color(item_id=id, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rope_product_color(
    id: int,
    service: RopeProductColorService = Depends(get_rope_product_color_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Unlink a color from a rope product (admin only)."""
    await service.delete_rope_product_color(item_id=id)
