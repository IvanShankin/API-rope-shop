from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.products.depends import get_product_service
from src.modules.products.models_dto import (
    ProductCreate,
    ProductLocalizedResponseDTO,
    ProductResponseDTO,
    ProductTranslationCreate,
    ProductTranslationResponseDTO,
    ProductTranslationUpdate,
    ProductUpdate,
    ProductUpdateIndexDTO,
)
from src.modules.products.service import ProductService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=List[ProductLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all products",
    description="Get products with localized content. Supports filtering by category, type, active status, and pagination (public).",
)
async def get_all_products(
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    category_slug: Optional[str] = Query(None, description="Filter by category slug"),
    product_type: Optional[str] = Query(None, description="Filter by product type (rope, finished_product, hardware)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, description="Pagination limit"),
    service: ProductService = Depends(get_product_service),
) -> List[ProductLocalizedResponseDTO]:
    return await service.get_all_products(
        category_id=category_id,
        category_slug=category_slug,
        product_type=product_type,
        is_active=is_active,
        locale=locale,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/by-slug/{slug}",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get product by slug",
    description="Get full product details with all translations by slug (public).",
)
async def get_product_by_slug(
    slug: str,
    service: ProductService = Depends(get_product_service),
) -> ProductResponseDTO:
    return await service.get_product_by_slug(slug=slug)


@router.get(
    "/{product_id}",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
    description="Get full product details with all translations by ID (public).",
)
async def get_product_by_id(
    product_id: int,
    service: ProductService = Depends(get_product_service),
) -> ProductResponseDTO:
    return await service.get_product_by_id(product_id=product_id)


@router.post(
    "",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new catalog product with translations (admin only).",
)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductResponseDTO:
    return await service.create_product(data=data)


@router.patch(
    "/{product_id}",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update product",
    description="Update product attributes (category_id, slug, product_type, is_active) (admin only).",
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductResponseDTO:
    return await service.update_product(product_id=product_id, data=data)


@router.patch(
    "/{product_id}/index",
    response_model=ProductResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder product",
    description="Update product order index with automatic neighbor shifting (admin only).",
)
async def reorder_product(
    product_id: int,
    data: ProductUpdateIndexDTO,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductResponseDTO:
    return await service.reorder_product(product_id=product_id, data=data)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Delete product if it has no associated dependencies (admin only).",
)
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_product(product_id=product_id)


@router.post(
    "/{product_id}/translations",
    response_model=ProductTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add product translation",
    description="Add a new localized translation for product (admin only).",
)
async def add_translation(
    product_id: int,
    data: ProductTranslationCreate,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductTranslationResponseDTO:
    return await service.create_translation(product_id=product_id, data=data)


@router.patch(
    "/translations/{translation_id}",
    response_model=ProductTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update product translation",
    description="Update product translation name or description (admin only).",
)
async def update_translation(
    translation_id: int,
    data: ProductTranslationUpdate,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductTranslationResponseDTO:
    return await service.update_translation(
        translation_id=translation_id,
        data=data,
    )


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product translation",
    description="Delete a translation (forbidden to delete the only remaining translation) (admin only).",
)
async def delete_translation(
    translation_id: int,
    service: ProductService = Depends(get_product_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_translation(
        translation_id=translation_id,
    )
