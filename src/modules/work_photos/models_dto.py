from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO


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
    index: Optional[int] = Field(None, ge=0, description="Optional sort index")
    is_active: bool = Field(True, description="Active status")


class UpdateWorkPhotoRequestDTO(BaseModel):
    image_url: Optional[str] = Field(None, max_length=500, description="URL of the photo")
    title: Optional[str] = Field(None, max_length=255, description="Title of the photo")
    description: Optional[str] = Field(None, description="Description of the photo")
    is_active: Optional[bool] = Field(None, description="Active status")


class UpdateWorkPhotoIndexRequestDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New sort order index")


class WorkPhotoResponseDTO(ORMDTO):
    id: int
    image_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    index: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
