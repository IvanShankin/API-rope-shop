from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, status

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.product_application.depends import get_product_application_service
from src.modules.product_application.models_dto import (
    AssignApplicationToProductDTO,
    ProductApplicationCreate,
    ProductApplicationLocalizedResponseDTO,
    ProductApplicationResponseDTO,
    ProductApplicationTranslationCreate,
    ProductApplicationTranslationResponseDTO,
    ProductApplicationTranslationUpdate,
    ProductApplicationUpdate,
    ProductApplicationUpdateIndexDTO,
    ProductAssignedApplicationResponseDTO,
)
from src.modules.product_application.service import ProductApplicationService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/product_applications", tags=["Product Applications"])


# ==================== Application Directory Endpoints ====================


@router.get(
    "",
    response_model=Union[List[ProductApplicationLocalizedResponseDTO], List[ProductApplicationResponseDTO]],
    status_code=status.HTTP_200_OK,
    summary="Get all applications",
    description="Get all product applications directory (public). If locale is passed, returns localized flat items, otherwise returns full models with all translations.",
)
async def get_all_applications(
    locale: Optional[Language] = Query(None, description="Language for translation localization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Offset"),
    limit: Optional[int] = Query(None, ge=1, description="Limit"),
    service: ProductApplicationService = Depends(get_product_application_service),
):
    return await service.get_all_applications(
        locale=locale,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/by-code/{code}",
    response_model=ProductApplicationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get application by code",
    description="Get application details by unique code (e.g. winch, sheet) (public).",
)
async def get_application_by_code(
    code: str,
    service: ProductApplicationService = Depends(get_product_application_service),
) -> ProductApplicationResponseDTO:
    return await service.get_application_by_code(code=code)


@router.get(
    "/{id}",
    response_model=ProductApplicationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get application by ID",
    description="Get application details by ID with all translations (public).",
)
async def get_application_by_id(
    id: int,
    service: ProductApplicationService = Depends(get_product_application_service),
) -> ProductApplicationResponseDTO:
    return await service.get_application_by_id(app_id=id)


@router.post(
    "",
    response_model=ProductApplicationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create application",
    description="Create a new application in directory with translations (admin only).",
)
async def create_application(
    data: ProductApplicationCreate,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductApplicationResponseDTO:
    return await service.create_application(data=data)


@router.patch(
    "/{id}",
    response_model=ProductApplicationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update application",
    description="Update application attributes (code, is_active) (admin only).",
)
async def update_application(
    id: int,
    data: ProductApplicationUpdate,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductApplicationResponseDTO:
    return await service.update_application(app_id=id, data=data)


@router.patch(
    "/{id}/index",
    response_model=ProductApplicationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder application index",
    description="Update display order of application with automatic neighbor shifting (admin only).",
)
async def reorder_application(
    id: int,
    data: ProductApplicationUpdateIndexDTO,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductApplicationResponseDTO:
    return await service.reorder_application(app_id=id, data=data)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete application",
    description="Delete application by ID (forbidden if assigned to products) (admin only).",
)
async def delete_application(
    id: int,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_application(app_id=id)


# ==================== Translation Endpoints ====================


@router.post(
    "/{id}/translations",
    response_model=ProductApplicationTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add application translation",
    description="Add a new locale translation for an application (admin only).",
)
async def add_application_translation(
    id: int,
    data: ProductApplicationTranslationCreate,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductApplicationTranslationResponseDTO:
    return await service.add_translation(app_id=id, data=data)


@router.patch(
    "/{id}/translations/{locale}",
    response_model=ProductApplicationTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update application translation",
    description="Update an existing locale translation (admin only).",
)
async def update_application_translation(
    id: int,
    locale: Language,
    data: ProductApplicationTranslationUpdate,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductApplicationTranslationResponseDTO:
    return await service.update_translation(app_id=id, locale=locale, data=data)


@router.delete(
    "/{id}/translations/{locale}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete application translation",
    description="Delete translation for a locale (cannot delete last translation) (admin only).",
)
async def delete_application_translation(
    id: int,
    locale: Language,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_translation(app_id=id, locale=locale)


# ==================== Product Assignment Endpoints ====================


@router.get(
    "/by-product/{product_id}",
    response_model=List[ProductApplicationLocalizedResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get product applications",
    description="Get all applications assigned to a specific product (public).",
)
async def get_product_applications(
    product_id: int,
    locale: Optional[Language] = Query(None, description="Language for application name localization"),
    service: ProductApplicationService = Depends(get_product_application_service),
) -> List[ProductApplicationLocalizedResponseDTO]:
    return await service.get_product_applications(product_id=product_id, locale=locale)


@router.post(
    "/by-product/{product_id}",
    response_model=ProductAssignedApplicationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Assign application to product",
    description="Assign an application to a product (admin only).",
)
async def assign_application_to_product(
    product_id: int,
    data: AssignApplicationToProductDTO,
    locale: Optional[Language] = Query(None, description="Language for localized application response"),
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductAssignedApplicationResponseDTO:
    return await service.assign_to_product(product_id=product_id, data=data, locale=locale)


@router.delete(
    "/by-product/{product_id}/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unassign application from product",
    description="Remove assignment of an application from a product (admin only).",
)
async def unassign_application_from_product(
    product_id: int,
    application_id: int,
    service: ProductApplicationService = Depends(get_product_application_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.unassign_from_product(product_id=product_id, application_id=application_id)
