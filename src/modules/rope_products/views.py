from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from src.modules.check_permission.depends import get_current_admin, get_optional_admin
from src.modules.users.models_dto import UserDTO
from src.modules.rope_products.depends import get_rope_products_service
from src.modules.rope_products.service import RopeProductsService
from src.modules.rope_products.models_dto import (
    RopeConfiguratorSettingCreate,
    RopeConfiguratorSettingUpdate,
    RopeConfiguratorSettingResponseDTO,
    RopeConfiguratorSettingDetailResponseDTO,
    ProductVariantCreate,
    ProductVariantCreateForProduct,
    ProductVariantUpdate,
    ProductVariantUpdateIndexDTO,
    ProductVariantResponseDTO,
)

router = APIRouter(
    prefix="/rope_products",
    tags=["Rope Products (Admin & Internal Settings)"],
)
variants_router = APIRouter(prefix="/rope_variants", tags=["Rope Variants (Admin & Internal Settings)"])


# ==================== RopeConfiguratorSetting Endpoints ====================

@router.get(
    "",
    response_model=List[RopeConfiguratorSettingResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_all_rope_products(
    material_group_id: Optional[int] = Query(None, description="Filter by material group ID"),
    can_be_spliced: Optional[bool] = Query(None, description="Filter by spliceability"),
    service: RopeProductsService = Depends(get_rope_products_service),
    is_admin: bool = Depends(get_optional_admin),
):
    """
    Get list of rope configurator settings (admin/internal settings).
    Note: For client-facing configurator initialization bundle (including cached price rules,
    extras, splice types, and localized rope data in a single request), use GET /configurators.
    """
    return await service.get_all_rope_products(
        material_group_id=material_group_id,
        can_be_spliced=can_be_spliced,
        is_admin=is_admin,
    )


@router.get(
    "/{product_id}",
    response_model=RopeConfiguratorSettingDetailResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_rope_product(
    product_id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
    is_admin: bool = Depends(get_optional_admin),
):
    """Get rope configurator setting by product ID with variants, colors and allowed splices (public)."""
    return await service.get_rope_product(product_id=product_id, is_admin=is_admin)


@router.post(
    "",
    response_model=RopeConfiguratorSettingResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_rope_product(
    data: RopeConfiguratorSettingCreate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create rope configurator setting (admin only)."""
    return await service.create_rope_product(data=data)


@router.patch(
    "/{product_id}",
    response_model=RopeConfiguratorSettingResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_rope_product(
    product_id: int,
    data: RopeConfiguratorSettingUpdate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update rope configurator setting properties (admin only)."""
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
    """Delete rope configurator setting (admin only)."""
    await service.delete_rope_product(product_id=product_id)


# ==================== ProductVariant Endpoints under /rope_products/{product_id}/variants ====================

@router.get(
    "/{product_id}/variants",
    response_model=List[ProductVariantResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_variants_for_product(
    product_id: int,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: RopeProductsService = Depends(get_rope_products_service),
    is_admin: bool = Depends(get_optional_admin),
):
    """Get all variants of a product sorted by index (public)."""
    return await service.get_variants_for_product(product_id=product_id, is_active=is_active, is_admin=is_admin)


@router.post(
    "/{product_id}/variants",
    response_model=ProductVariantResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_variant_for_product(
    product_id: int,
    data: ProductVariantCreateForProduct,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Add a variant directly to a product (admin only)."""
    return await service.create_variant_for_product(product_id=product_id, data=data)


# ==================== Standalone ProductVariant Endpoints under /rope_variants ====================

@variants_router.post(
    "",
    response_model=ProductVariantResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_variant(
    data: ProductVariantCreate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Create a variant specifying product_id (admin only)."""
    return await service.create_variant(data=data)


@variants_router.get(
    "/{id}",
    response_model=ProductVariantResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_variant_by_id(
    id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
    is_admin: bool = Depends(get_optional_admin),
):
    """Get variant by ID (public)."""
    return await service.get_variant_by_id(variant_id=id, is_admin=is_admin)


@variants_router.patch(
    "/{id}",
    response_model=ProductVariantResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_variant(
    id: int,
    data: ProductVariantUpdate,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Update variant properties (admin only)."""
    return await service.update_variant(variant_id=id, data=data)


@variants_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_variant(
    id: int,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Delete variant (admin only)."""
    await service.delete_variant(variant_id=id)


@variants_router.patch(
    "/{id}/index",
    response_model=List[ProductVariantResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def update_variant_index(
    id: int,
    data: ProductVariantUpdateIndexDTO,
    service: RopeProductsService = Depends(get_rope_products_service),
    admin: UserDTO = Depends(get_current_admin),
):
    """Change variant display order index (admin only)."""
    return await service.update_variant_index(variant_id=id, data=data)
