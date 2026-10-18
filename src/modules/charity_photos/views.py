from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status

from src.modules.base.database_model import Language
from src.modules.charity_photos.depends import get_charity_photo_service
from src.modules.charity_photos.models_dto import (
    CharityPhotoResponseDTO,
    CharityPhotoTranslationCreate,
    CharityPhotoTranslationResponseDTO,
    CharityPhotoTranslationUpdate,
    UpdateCharityPhotoIndexRequestDTO,
    UpdateCharityPhotoRequestDTO,
)
from src.modules.charity_photos.service import CharityPhotoService
from src.modules.check_permission.depends import get_current_admin
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/charity_photos", tags=["Charity Photos"])


@router.get(
    "",
    response_model=List[CharityPhotoResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all charity photos",
    description="Get list of charity photos ordered by index (public). Supports pagination, status filtering, and localization.",
)
async def get_all_charity_photos(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    locale: Optional[Language] = Query(None, description="Preferred language for title and description"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, description="Pagination limit"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
) -> List[CharityPhotoResponseDTO]:
    return await service.get_photos(
        is_active=is_active,
        locale=locale,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{photo_id}",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get charity photo by ID",
    description="Get detailed charity photo data by ID with localized title/description and all translations (public).",
)
async def get_charity_photo_by_id(
    photo_id: int,
    locale: Optional[Language] = Query(None, description="Preferred language for title and description"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
) -> CharityPhotoResponseDTO:
    return await service.get_photo_by_id(photo_id=photo_id, locale=locale)


@router.post(
    "",
    response_model=CharityPhotoResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload charity photo file",
    description="Upload an image file, convert to WebP and create a CharityPhoto record with optional localized translation (admin only).",
)
async def create_charity_photo(
    file: UploadFile = File(..., description="Image file (jpg, png, webp, etc.)"),
    title: Optional[str] = Form(None, description="Title of the photo"),
    description: Optional[str] = Form(None, description="Description of the photo"),
    locale: Language = Form(Language.ENG, description="Locale for title and description"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    return await service.upload_photo(
        file=file,
        title=title,
        description=description,
        locale=locale,
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
    locale: Language = Form(Language.ENG, description="Locale for title and description"),
    index: Optional[int] = Form(None, ge=0, description="Optional sort index"),
    is_active: bool = Form(True, description="Active status"),
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoResponseDTO:
    return await service.upload_photo(
        file=file,
        title=title,
        description=description,
        locale=locale,
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
    locale: Optional[Language] = Form(None, description="Locale for title and description"),
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
                if locale is None and "locale" in body:
                    locale = Language(body["locale"])
        except Exception:
            pass

    data_dict = {}
    if title is not None:
        data_dict["title"] = title
    if description is not None:
        data_dict["description"] = description
    if locale is not None:
        data_dict["locale"] = locale
    if is_active is not None:
        data_dict["is_active"] = is_active
    data = UpdateCharityPhotoRequestDTO(**data_dict) if data_dict else None

    return await service.update_photo(photo_id=photo_id, data=data, file=file, locale=locale)


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


# ============================================================================
# Admin Endpoints: Translations Management
# ============================================================================


@router.post(
    "/{photo_id}/translations",
    response_model=CharityPhotoTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add charity photo translation",
    description="Add a new language translation for an existing charity photo (admin only).",
)
async def add_charity_photo_translation(
    photo_id: int,
    data: CharityPhotoTranslationCreate,
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoTranslationResponseDTO:
    return await service.add_translation(photo_id=photo_id, data=data)


@router.patch(
    "/{photo_id}/translations/{translation_id}",
    response_model=CharityPhotoTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update charity photo translation",
    description="Update title/description of a specific charity photo translation (admin only).",
)
async def update_charity_photo_translation(
    photo_id: int,
    translation_id: int,
    data: CharityPhotoTranslationUpdate,
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> CharityPhotoTranslationResponseDTO:
    return await service.update_translation(
        photo_id=photo_id,
        translation_id=translation_id,
        data=data,
    )


@router.delete(
    "/{photo_id}/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete charity photo translation",
    description="Delete a translation of a charity photo. Cannot delete the last remaining translation (admin only).",
)
async def delete_charity_photo_translation(
    photo_id: int,
    translation_id: int,
    service: CharityPhotoService = Depends(get_charity_photo_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_translation(
        photo_id=photo_id,
        translation_id=translation_id,
    )
