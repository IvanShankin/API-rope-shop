from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO
from src.modules.products.models import ProductType


# ===================== Translation DTOs =====================


class ProductTranslationBase(BaseModel):
    locale: Language
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProductTranslationCreate(ProductTranslationBase):
    pass


class ProductTranslationInsert(ProductTranslationCreate):
    product_id: int


class ProductTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class ProductTranslationResponseDTO(ProductTranslationBase, ORMDTO):
    id: int
    product_id: int


# ===================== Product DTOs =====================


class ProductBase(BaseModel):
    category_id: int = Field(..., gt=0)
    slug: str = Field(..., min_length=1, max_length=150)
    product_type: str = Field(ProductType.ROPE.value, min_length=1, max_length=50)
    index: int = Field(..., ge=0)
    is_active: bool = True


class ProductCreate(BaseModel):
    category_id: int = Field(..., gt=0, description="Category ID this product belongs to")
    slug: str = Field(..., min_length=1, max_length=150, description="Unique human-readable slug")
    product_type: str = Field(
        ProductType.ROPE.value,
        min_length=1,
        max_length=50,
        description="Type of product (rope, finished_product, hardware)",
    )
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Optional position index; if not provided, max_index + 1 will be used",
    )
    is_active: bool = True
    translations: List[ProductTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating a Product",
    )


class ProductUpdate(BaseModel):
    category_id: Optional[int] = Field(None, gt=0)
    slug: Optional[str] = Field(None, min_length=1, max_length=150)
    product_type: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class ProductUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class ProductResponseDTO(ProductBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    translations: List[ProductTranslationResponseDTO] = []
    main_image_url: Optional[str] = None


class ProductLocalizedResponseDTO(ORMDTO):
    id: int
    category_id: Optional[int]
    slug: Optional[str]
    product_type: str
    index: int
    is_active: bool
    name: str
    description: Optional[str] = None
    main_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
