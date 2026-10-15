from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.product_specification.depends import get_product_specification_service
from src.modules.product_specification.models_dto import (
    ProductSpecificationBatchCreate,
    ProductSpecificationBatchDelete,
    ProductSpecificationBatchDeleteResponseDTO,
    ProductSpecificationBatchSync,
    ProductSpecificationBatchUpdate,
    ProductSpecificationCreate,
    ProductSpecificationLocalizedResponseDTO,
    ProductSpecificationResponseDTO,
    ProductSpecificationTranslationCreate,
    ProductSpecificationTranslationResponseDTO,
    ProductSpecificationTranslationUpdate,
    ProductSpecificationUpdate,
    ProductSpecificationUpdateIndexDTO,
)
from src.modules.product_specification.service import ProductSpecificationService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/product_specifications", tags=["Product Specifications"])


# ==================== Batch Endpoints ====================


@router.get(
    "/by-product/{product_id}",
    response_model=Union[List[ProductSpecificationLocalizedResponseDTO], List[ProductSpecificationResponseDTO]],
    status_code=status.HTTP_200_OK,
    summary="Get product specifications",
    description="Get all specifications for a product ordered by index (public).",
)
async def get_specifications_by_product(
    product_id: int,
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    service: ProductSpecificationService = Depends(get_product_specification_service),
):
    return await service.get_by_product_id(product_id=product_id, locale=locale)


@router.post(
    "/by-product/{product_id}/batch",
    response_model=List[ProductSpecificationResponseDTO],
    status_code=status.HTTP_201_CREATED,
    summary="Batch create product specifications",
    description="Create multiple specifications for a product in one request (admin only).",
)
async def batch_create_specifications(
    product_id: int,
    data: ProductSpecificationBatchCreate,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> List[ProductSpecificationResponseDTO]:
    return await service.create_batch(product_id=product_id, data=data)


@router.put(
    "/by-product/{product_id}/batch",
    response_model=List[ProductSpecificationResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Batch update product specifications",
    description="Update multiple specifications for a product in one request (admin only).",
)
async def batch_update_specifications(
    product_id: int,
    data: ProductSpecificationBatchUpdate,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> List[ProductSpecificationResponseDTO]:
    return await service.update_batch(product_id=product_id, data=data)


@router.delete(
    "/by-product/{product_id}/batch",
    response_model=ProductSpecificationBatchDeleteResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Batch delete product specifications",
    description="Delete multiple specifications for a product in one request (admin only).",
)
async def batch_delete_specifications(
    product_id: int,
    data: ProductSpecificationBatchDelete,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductSpecificationBatchDeleteResponseDTO:
    return await service.delete_batch(product_id=product_id, data=data)


@router.put(
    "/by-product/{product_id}/sync",
    response_model=List[ProductSpecificationResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Sync all product specifications",
    description="Full synchronization of product specifications (create, update, delete in one list) (admin only).",
)
async def sync_product_specifications(
    product_id: int,
    data: ProductSpecificationBatchSync,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> List[ProductSpecificationResponseDTO]:
    return await service.sync_batch(product_id=product_id, data=data)


@router.delete(
    "/by-product/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all specifications of a product",
    description="Delete all specifications for the specified product (admin only).",
)
async def delete_all_specifications_of_product(
    product_id: int,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_all_by_product(product_id=product_id)


# ==================== Single CRUD Endpoints ====================


@router.post(
    "",
    response_model=ProductSpecificationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create single specification",
    description="Create a single specification for a product (admin only).",
)
async def create_specification(
    data: ProductSpecificationCreate,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductSpecificationResponseDTO:
    return await service.create_specification(data=data)


@router.get(
    "/{id}",
    response_model=ProductSpecificationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get specification by ID",
    description="Get full specification details by ID with all translations (public).",
)
async def get_specification_by_id(
    id: int,
    service: ProductSpecificationService = Depends(get_product_specification_service),
) -> ProductSpecificationResponseDTO:
    return await service.get_by_id(spec_id=id)


@router.patch(
    "/{id}",
    response_model=ProductSpecificationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update single specification",
    description="Update specification attributes (index, translations) (admin only).",
)
async def update_specification(
    id: int,
    data: ProductSpecificationUpdate,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductSpecificationResponseDTO:
    return await service.update_specification(spec_id=id, data=data)


@router.patch(
    "/{id}/index",
    response_model=ProductSpecificationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder specification index",
    description="Update display index of a specification within a product (admin only).",
)
async def reorder_specification(
    id: int,
    data: ProductSpecificationUpdateIndexDTO,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductSpecificationResponseDTO:
    return await service.reorder_specification(spec_id=id, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete single specification",
    description="Delete a specification by ID (admin only).",
)
async def delete_specification(
    id: int,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_specification(spec_id=id)


# ==================== Translation Endpoints ====================


@router.post(
    "/{id}/translations",
    response_model=ProductSpecificationTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add specification translation",
    description="Add or update a translation for a specification (admin only).",
)
async def add_specification_translation(
    id: int,
    data: ProductSpecificationTranslationCreate,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductSpecificationTranslationResponseDTO:
    return await service.add_translation(spec_id=id, data=data)


@router.patch(
    "/{id}/translations/{locale}",
    response_model=ProductSpecificationTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update specification translation",
    description="Update a specific translation for a specification (admin only).",
)
async def update_specification_translation(
    id: int,
    locale: Language,
    data: ProductSpecificationTranslationUpdate,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductSpecificationTranslationResponseDTO:
    return await service.update_translation(spec_id=id, locale=locale, data=data)


@router.delete(
    "/{id}/translations/{locale}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete specification translation",
    description="Delete a translation of a specification (cannot delete last translation) (admin only).",
)
async def delete_specification_translation(
    id: int,
    locale: Language,
    service: ProductSpecificationService = Depends(get_product_specification_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_translation(spec_id=id, locale=locale)
