from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO


# ==================== Translation DTOs ====================


class WorkPhotoTranslationCreate(BaseModel):
    locale: Language = Field(..., description="Language code for the translation")
    title: Optional[str] = Field(None, max_length=255, description="Title of the photo")
    description: Optional[str] = Field(None, description="Description of the photo")


class WorkPhotoTranslationUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Updated title")
    description: Optional[str] = Field(None, description="Updated description")


class WorkPhotoTranslationResponseDTO(ORMDTO):
    id: int
    work_photo_id: int
    locale: Language
    title: Optional[str] = None
    description: Optional[str] = None


class WorkPhotoTranslationInsert(BaseModel):
    work_photo_id: int
    locale: Language
    title: Optional[str] = None
    description: Optional[str] = None


# ==================== Photo DTOs ====================


class WorkPhotoBaseDTO(BaseModel):
    image_url: str = Field(..., max_length=500, description="URL of the photo")
    title: Optional[str] = Field(None, max_length=255, description="Title of the photo")
    description: Optional[str] = Field(None, description="Description of the photo")
    index: int = Field(0, ge=0, description="Sort order index")
    is_active: bool = Field(True, description="Active status")


class CreateWorkPhotoRequestDTO(BaseModel):
    image_url: str = Field(..., max_length=500, description="URL of the photo")
    title: Optional[str] = Field(None, max_length=255, description="Title of the photo")
    description: Optional[str] = Field(None, description="Description of the photo")
    locale: Language = Field(Language.ENG, description="Locale for initial translation")
    index: Optional[int] = Field(None, ge=0, description="Optional sort index")
    is_active: bool = Field(True, description="Active status")
    translations: Optional[List[WorkPhotoTranslationCreate]] = Field(
        None, description="Optional list of translations"
    )


class UpdateWorkPhotoRequestDTO(BaseModel):
    title: Optional[str] = Field(None, max_length=255, description="Title of the photo")
    description: Optional[str] = Field(None, description="Description of the photo")
    locale: Optional[Language] = Field(None, description="Locale for updated title/description")
    is_active: Optional[bool] = Field(None, description="Active status")


class UpdateWorkPhotoIndexRequestDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New sort order index")


class WorkPhotoResponseDTO(ORMDTO):
    id: int
    image_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    locale: Optional[Language] = None
    translations: List[WorkPhotoTranslationResponseDTO] = []
    index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
