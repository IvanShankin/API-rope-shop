from typing import List, Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import (
    get_current_admin,
    get_optional_admin,
)
from src.modules.categories.depends import get_category_service
from src.modules.categories.models_dto import (
    CategoryCreate,
    CategoryListResponseDTO,
    CategoryLocalizedResponseDTO,
    CategoryResponseDTO,
    CategoryTranslationCreate,
    CategoryTranslationResponseDTO,
    CategoryTranslationUpdate,
    CategoryUpdate,
    CategoryUpdateIndexDTO,
)
from src.modules.categories.service import CategoryService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get(
    "",
    response_model=CategoryListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get all categories",
    description="Get all categories with localized names and product counts (public). Supports pagination and status filtering (admin only for inactive).",
)
async def get_all_categories(
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (admin only)"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, description="Pagination limit"),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: CategoryService = Depends(get_category_service),
) -> CategoryListResponseDTO:
    return await service.get_all_categories(
        locale=locale,
        is_active=is_active,
        skip=skip,
        limit=limit,
        is_admin=admin is not None,
    )


@router.get(
    "/by-slug/{slug}",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get category by slug",
    description="Get full category details with all translations by slug (public). Inactive categories accessible to admin only.",
)
async def get_category_by_slug(
    slug: str,
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponseDTO:
    return await service.get_category_by_slug(slug=slug, is_admin=admin is not None)


@router.get(
    "/{category_id}",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get category by ID",
    description="Get full category details with all translations by ID (public). Inactive categories accessible to admin only.",
)
async def get_category_by_id(
    category_id: int,
    admin: Optional[UserDTO] = Depends(get_optional_admin),
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponseDTO:
    return await service.get_category_by_id(category_id=category_id, is_admin=admin is not None)


@router.post(
    "",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Create a new category with translations (admin only).",
)
async def create_category(
    data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryResponseDTO:
    return await service.create_category(data=data)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update category",
    description="Update category attributes (slug, is_active) (admin only).",
)
async def update_category(
    category_id: int,
    data: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryResponseDTO:
    return await service.update_category(category_id=category_id, data=data)


@router.patch(
    "/{category_id}/index",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder category",
    description="Update category order index with automatic neighbor shifting (admin only).",
)
async def reorder_category(
    category_id: int,
    data: CategoryUpdateIndexDTO,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryResponseDTO:
    return await service.reorder_category(category_id=category_id, data=data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Delete category if it has no associated products (admin only).",
)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_category(category_id=category_id)


@router.post(
    "/{category_id}/image",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload category image",
    description="Upload, convert to WebP and save category image (admin only).",
)
async def upload_category_image(
    category_id: int,
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryResponseDTO:
    return await service.upload_image(category_id=category_id, file=file)


@router.delete(
    "/{category_id}/image",
    response_model=CategoryResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete category image",
    description="Delete category image from disk and DB (admin only).",
)
async def delete_category_image(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryResponseDTO:
    return await service.delete_image(category_id=category_id)


@router.post(
    "/{category_id}/translations",
    response_model=CategoryTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add category translation",
    description="Add a new localized translation for category (admin only).",
)
async def add_translation(
    category_id: int,
    data: CategoryTranslationCreate,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryTranslationResponseDTO:
    return await service.create_translation(category_id=category_id, data=data)


@router.patch(
    "/translations/{translation_id}",
    response_model=CategoryTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update category translation",
    description="Update translation name (admin only).",
)
async def update_translation(
    translation_id: int,
    data: CategoryTranslationUpdate,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CategoryTranslationResponseDTO:
    return await service.update_translation(
        translation_id=translation_id,
        data=data,
    )


@router.delete(
    "/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category translation",
    description="Delete a translation (forbidden to delete the only remaining translation) (admin only).",
)
async def delete_translation(
    translation_id: int,
    service: CategoryService = Depends(get_category_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_translation(
        translation_id=translation_id,
    )
