from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO, PaginatedResponse


# ===================== Translation DTOs =====================


class CategoryTranslationBase(BaseModel):
    locale: Language
    name: str = Field(..., min_length=1, max_length=255)


class CategoryTranslationCreate(CategoryTranslationBase):
    pass


class CategoryTranslationInsert(CategoryTranslationCreate):
    category_id: int


class CategoryTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class CategoryTranslationResponseDTO(CategoryTranslationBase, ORMDTO):
    id: int
    category_id: int


# ===================== Category DTOs =====================


class CategoryBase(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    image_url: Optional[str] = Field(None, max_length=500)
    index: int = Field(..., ge=0)
    is_active: bool = True


class CategoryCreate(BaseModel):
    slug: str = Field(..., min_length=1, max_length=100)
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Optional position index; if not provided, max_index + 1 will be used",
    )
    is_active: bool = True
    translations: List[CategoryTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating a Category",
    )


class CategoryUpdate(BaseModel):
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class CategoryUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class CategoryResponseDTO(CategoryBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    translations: List[CategoryTranslationResponseDTO] = []
    products_count: int = 0


class CategoryLocalizedResponseDTO(CategoryBase, ORMDTO):
    id: int
    name: str
    products_count: int = 0
    created_at: datetime
    updated_at: datetime


class CategoryListResponseDTO(PaginatedResponse[CategoryLocalizedResponseDTO]):
    """Ответ со списком категорий и метаданными пагинации."""
    pass
