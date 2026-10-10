from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.rope_products.models_dto import (
    RopeProductCreate,
    RopeProductUpdate,
    RopeProductResponseDTO,
    RopeProductDetailResponseDTO,
    RopeVariantCreate,
    RopeVariantCreateForProduct,
    RopeVariantUpdate,
    RopeVariantUpdateIndexDTO,
    RopeVariantResponseDTO,
)
from src.modules.rope_products.service import RopeProductsService
from src.modules.rope_products.depends import get_rope_products_service

router = APIRouter(prefix="/rope_products", tags=["Rope Products"])
variants_router = APIRouter(prefix="/rope_variants", tags=["Rope Variants"])


# ==================== RopeProduct Endpoints ====================

@router.get(
    "",
    response_model=List[RopeProductResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def list_rope_products(
    material_group_id: Optional[int] = Query(None, description="Filter by material group ID"),
    can_be_spliced: Optional[bool] = Query(None, description="Filter by spliceability"),
    service: RopeProductsService = Depends(get_rope_products_service),
):
    """Get list of rope products with filters (public)."""
    return await service.list_rope_products(
        material_group_id=material_group_id,
        can_be_spliced=can_be_spliced,
    )


@router.get(
    "/{product_id}",
    response_model=RopeProductDetailResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_rope_product(
    product_id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
):
    """Get detailed rope product info including variants, colors, allowed splices (public)."""
    return await service.get_rope_product(product_id=product_id)


@router.post(
    "",
    response_model=RopeProductResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_rope_product(
    data: RopeProductCreate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new rope product (admin only)."""
    return await service.create_rope_product(data=data)


@router.patch(
    "/{product_id}",
    response_model=RopeProductResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_rope_product(
    product_id: int,
    data: RopeProductUpdate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update rope product properties (admin only)."""
    return await service.update_rope_product(product_id=product_id, data=data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rope_product(
    product_id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete rope product (admin only)."""
    await service.delete_rope_product(product_id=product_id)


# ==================== RopeVariant nested under /rope_products ====================

@router.get(
    "/{product_id}/variants",
    response_model=List[RopeVariantResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def list_product_variants(
    product_id: int,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: RopeProductsService = Depends(get_rope_products_service),
):
    """Get all variants for a specific rope product ordered by index (public)."""
    return await service.get_variants_by_product_id(
        rope_product_id=product_id,
        is_active=is_active,
    )


@router.post(
    "/{product_id}/variants",
    response_model=RopeVariantResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_variant_for_product(
    product_id: int,
    data: RopeVariantCreateForProduct,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new variant/diameter for a rope product (admin only)."""
    full_data = RopeVariantCreate(
        rope_product_id=product_id,
        diameter_mm=data.diameter_mm,
        breaking_load_dan=data.breaking_load_dan,
        weight_g_per_m=data.weight_g_per_m,
        price_per_meter=data.price_per_meter,
        is_active=data.is_active,
    )
    return await service.create_variant(data=full_data)


# ==================== RopeVariant standalone endpoints ====================

@variants_router.post(
    "",
    response_model=RopeVariantResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_variant(
    data: RopeVariantCreate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a new variant/diameter specifying rope_product_id (admin only)."""
    return await service.create_variant(data=data)


@variants_router.get(
    "/{id}",
    response_model=RopeVariantResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_variant(
    id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
):
    """Get variant by ID (public)."""
    return await service.get_variant_by_id(variant_id=id)


@variants_router.patch(
    "/{id}",
    response_model=RopeVariantResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_variant(
    id: int,
    data: RopeVariantUpdate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update variant properties (admin only)."""
    return await service.update_variant(variant_id=id, data=data)


@variants_router.patch(
    "/{id}/index",
    response_model=RopeVariantResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def reorder_variant(
    id: int,
    data: RopeVariantUpdateIndexDTO,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Reorder variant position within rope product with neighbors shift (admin only)."""
    return await service.reorder_variant(variant_id=id, data=data)


@variants_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_variant(
    id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete variant and collapse index gaps (admin only)."""
    await service.delete_variant(variant_id=id)
