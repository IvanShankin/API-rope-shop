from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status

from src.modules.check_permission.depends import get_current_admin
from src.modules.product_images.depends import get_product_image_service
from src.modules.product_images.models_dto import (
    ProductImageCreate,
    ProductImageResponseDTO,
    ProductImageUpdate,
    ProductImageUpdateIndexDTO,
)
from src.modules.product_images.service import ProductImageService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/product_images", tags=["Product Images"])


@router.get(
    "/by-product/{product_id}",
    response_model=List[ProductImageResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get product images",
    description="Get all images for a specific product ordered by index (public).",
)
async def get_images_by_product(
    product_id: int,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: ProductImageService = Depends(get_product_image_service),
) -> List[ProductImageResponseDTO]:
    return await service.get_images_by_product(
        product_id=product_id,
        is_active=is_active,
    )


@router.get(
    "/{image_id}",
    response_model=ProductImageResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get product image by ID",
    description="Get detailed image data by ID (public).",
)
async def get_image_by_id(
    image_id: int,
    service: ProductImageService = Depends(get_product_image_service),
) -> ProductImageResponseDTO:
    return await service.get_image_by_id(image_id=image_id)


@router.post(
    "",
    response_model=ProductImageResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload product image file",
    description="Upload an image file, convert to WebP and create a ProductImage record (admin only).",
)
async def create_product_image(
    product_id: int = Form(..., description="ID of the product"),
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    is_main: bool = Form(False, description="Set as main product image"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: ProductImageService = Depends(get_product_image_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductImageResponseDTO:
    return await service.upload_image(
        product_id=product_id,
        file=file,
        is_main=is_main,
        index=index,
        is_active=is_active,
    )


@router.post(
    "/upload",
    response_model=ProductImageResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload product image file",
    description="Upload an image file, convert to WebP and create a ProductImage record (admin only).",
)
async def upload_product_image(
    product_id: int = Form(..., description="ID of the product"),
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    is_main: bool = Form(False, description="Set as main product image"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: ProductImageService = Depends(get_product_image_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductImageResponseDTO:
    return await service.upload_image(
        product_id=product_id,
        file=file,
        is_main=is_main,
        index=index,
        is_active=is_active,
    )


@router.patch(
    "/{image_id}",
    response_model=ProductImageResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update product image",
    description="Update image attributes (is_main, is_active) or replace image file (admin only).",
)
async def update_product_image(
    image_id: int,
    request: Request,
    file: Optional[UploadFile] = File(None, description="New image file to replace current"),
    is_main: Optional[bool] = Form(None, description="Set as main product image"),
    is_active: Optional[bool] = Form(None, description="Active status"),
    service: ProductImageService = Depends(get_product_image_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductImageResponseDTO:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if is_main is None and "is_main" in body:
                    is_main = body["is_main"]
                if is_active is None and "is_active" in body:
                    is_active = body["is_active"]
        except Exception:
            pass

    data_dict = {}
    if is_main is not None:
        data_dict["is_main"] = is_main
    if is_active is not None:
        data_dict["is_active"] = is_active
    data = ProductImageUpdate(**data_dict) if data_dict else None

    return await service.update_image(image_id=image_id, data=data, file=file)


@router.patch(
    "/{image_id}/main",
    response_model=ProductImageResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Set product image as main",
    description="Set specified image as main; other images of this product will have is_main=False (admin only).",
)
async def set_main_product_image(
    image_id: int,
    service: ProductImageService = Depends(get_product_image_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductImageResponseDTO:
    return await service.set_main_image(image_id=image_id)


@router.patch(
    "/{image_id}/index",
    response_model=ProductImageResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder product image",
    description="Update image order index with automatic neighbor shifting (admin only).",
)
async def reorder_product_image(
    image_id: int,
    data: ProductImageUpdateIndexDTO,
    service: ProductImageService = Depends(get_product_image_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ProductImageResponseDTO:
    return await service.reorder_image(image_id=image_id, data=data)


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product image",
    description="Delete image from DB and disk (admin only).",
)
async def delete_product_image(
    image_id: int,
    service: ProductImageService = Depends(get_product_image_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_image(image_id=image_id)
