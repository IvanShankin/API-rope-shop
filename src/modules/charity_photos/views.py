from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.charity_photos.depends import get_charity_photo_service
from src.modules.charity_photos.models_dto import (
    CharityPhotoResponseDTO,
    CreateCharityPhotoRequestDTO,
    UpdateCharityPhotoIndexRequestDTO,
    UpdateCharityPhotoRequestDTO,
)
from src.modules.charity_photos.service import CharityPhotoService

router = APIRouter(prefix="/charity_photos", tags=["Charity Photos"])


@router.get(
    "",
    response_model=List[CharityPhotoResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all charity photos",
    description="Get list of charity photos ordered by index (public). Supports pagination and status filtering.",
)
async def get_all_charity_photos(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, description="Pagination limit"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
) -> List[CharityPhotoResponseDTO]:
    return await service.get_photos(
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{photo_id}",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get charity photo by ID",
    description="Get detailed charity photo data by ID (public).",
)
async def get_charity_photo_by_id(
    photo_id: int,
    service: CharityPhotoService = Depends(get_charity_photo_service),
) -> CharityPhotoResponseDTO:
    return await service.get_photo_by_id(photo_id=photo_id)


@router.post(
    "",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload charity photo file",
    description="Upload an image file, convert to WebP and create a CharityPhoto record (admin only).",
)
async def create_charity_photo(
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    title: Optional[str] = Form(None, description="Title of the photo"),
    description: Optional[str] = Form(None, description="Description of the photo"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    return await service.upload_photo(
        file=file,
        title=title,
        description=description,
        index=index,
        is_active=is_active,
    )


@router.post(
    "/upload",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload charity photo file",
    description="Upload an image file, convert to WebP and create a CharityPhoto record (admin only).",
)
async def upload_charity_photo(
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    title: Optional[str] = Form(None, description="Title of the photo"),
    description: Optional[str] = Form(None, description="Description of the photo"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    return await service.upload_photo(
        file=file,
        title=title,
        description=description,
        index=index,
        is_active=is_active,
    )


@router.post(
    "/{photo_id}/upload-image",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload/replace image for existing charity photo",
    description="Upload a new image file, convert to WebP and replace the image of an existing CharityPhoto (admin only).",
)
async def upload_image_for_charity_photo(
    photo_id: int,
    file: UploadFile = File(..., description="Image file to replace current image"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    return await service.upload_image_for_photo(
        photo_id=photo_id,
        file=file,
    )


@router.patch(
    "/{photo_id}",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update charity photo",
    description="Update charity photo attributes (title, description, is_active) or replace image file (admin only).",
)
async def update_charity_photo(
    photo_id: int,
    request: Request,
    file: Optional[UploadFile] = File(None, description="Image file to replace current image"),
    title: Optional[str] = Form(None, description="Title of the photo"),
    description: Optional[str] = Form(None, description="Description of the photo"),
    is_active: Optional[bool] = Form(None, description="Active status"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                if title is None and "title" in body:
                    title = body["title"]
                if description is None and "description" in body:
                    description = body["description"]
                if is_active is None and "is_active" in body:
                    is_active = body["is_active"]
        except Exception:
            pass

    data_dict = {}
    if title is not None:
        data_dict["title"] = title
    if description is not None:
        data_dict["description"] = description
    if is_active is not None:
        data_dict["is_active"] = is_active
    data = UpdateCharityPhotoRequestDTO(**data_dict) if data_dict else None

    return await service.update_photo(photo_id=photo_id, data=data, file=file)


@router.patch(
    "/{photo_id}/index",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder charity photo",
    description="Update charity photo order index with automatic neighbor shifting (admin only).",
)
async def reorder_charity_photo(
    photo_id: int,
    data: UpdateCharityPhotoIndexRequestDTO,
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    return await service.reorder_photo(photo_id=photo_id, data=data)


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete charity photo",
    description="Delete charity photo from DB and disk (admin only).",
)
async def delete_charity_photo(
    photo_id: int,
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_photo(photo_id=photo_id)
