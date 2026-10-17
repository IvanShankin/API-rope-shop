from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO
from src.modules.work_photos.depends import get_work_photo_service
from src.modules.work_photos.models_dto import (
    CreateWorkPhotoRequestDTO,
    UpdateWorkPhotoIndexRequestDTO,
    UpdateWorkPhotoRequestDTO,
    WorkPhotoResponseDTO,
)
from src.modules.work_photos.service import WorkPhotoService

router = APIRouter(prefix="/work_photos", tags=["Work Photos"])


@router.get(
    "",
    response_model=List[WorkPhotoResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all work photos",
    description="Get list of work photos ordered by index (public). Supports pagination and status filtering.",
)
async def get_all_work_photos(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, description="Pagination limit"),
    service: WorkPhotoService = Depends(get_work_photo_service),
) -> List[WorkPhotoResponseDTO]:
    return await service.get_photos(
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{photo_id}",
    response_model=WorkPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get work photo by ID",
    description="Get detailed work photo data by ID (public).",
)
async def get_work_photo_by_id(
    photo_id: int,
    service: WorkPhotoService = Depends(get_work_photo_service),
) -> WorkPhotoResponseDTO:
    return await service.get_photo_by_id(photo_id=photo_id)


@router.post(
    "",
    response_model=WorkPhotoResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create work photo via JSON",
    description="Create a work photo record with an existing image URL (admin only).",
)
async def create_work_photo(
    data: CreateWorkPhotoRequestDTO,
    service: WorkPhotoService = Depends(get_work_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> WorkPhotoResponseDTO:
    return await service.create_photo(data=data)


@router.post(
    "/upload",
    response_model=WorkPhotoResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload work photo file",
    description="Upload an image file, convert to WebP and create a WorkPhoto record (admin only).",
)
async def upload_work_photo(
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    title: Optional[str] = Form(None, description="Title of the photo"),
    description: Optional[str] = Form(None, description="Description of the photo"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: WorkPhotoService = Depends(get_work_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> WorkPhotoResponseDTO:
    return await service.upload_photo(
        file=file,
        title=title,
        description=description,
        index=index,
        is_active=is_active,
    )


@router.post(
    "/{photo_id}/upload-image",
    response_model=WorkPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Upload/replace image for existing work photo",
    description="Upload a new image file, convert to WebP and replace the image of an existing WorkPhoto (admin only).",
)
async def upload_image_for_work_photo(
    photo_id: int,
    file: UploadFile = File(..., description="Image file to replace current image"),
    service: WorkPhotoService = Depends(get_work_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> WorkPhotoResponseDTO:
    return await service.upload_image_for_photo(
        photo_id=photo_id,
        file=file,
    )


@router.patch(
    "/{photo_id}",
    response_model=WorkPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update work photo",
    description="Update work photo attributes (title, description, image_url, is_active) (admin only).",
)
async def update_work_photo(
    photo_id: int,
    data: UpdateWorkPhotoRequestDTO,
    service: WorkPhotoService = Depends(get_work_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> WorkPhotoResponseDTO:
    return await service.update_photo(photo_id=photo_id, data=data)


@router.patch(
    "/{photo_id}/index",
    response_model=WorkPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder work photo",
    description="Update work photo order index with automatic neighbor shifting (admin only).",
)
async def reorder_work_photo(
    photo_id: int,
    data: UpdateWorkPhotoIndexRequestDTO,
    service: WorkPhotoService = Depends(get_work_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> WorkPhotoResponseDTO:
    return await service.reorder_photo(photo_id=photo_id, data=data)


@router.delete(
    "/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete work photo",
    description="Delete work photo from DB and disk (admin only).",
)
async def delete_work_photo(
    photo_id: int,
    service: WorkPhotoService = Depends(get_work_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_photo(photo_id=photo_id)
