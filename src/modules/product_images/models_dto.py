from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO


class ProductImageBase(BaseModel):
    product_id: int
    image_url: str = Field(..., max_length=500)
    is_main: bool = False
    index: int = Field(0, ge=0)
    is_active: bool = True


class ProductImageCreate(BaseModel):
    product_id: int
    image_url: str = Field(..., max_length=500)
    is_main: bool = False
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Optional position index; if not provided, max_index + 1 will be used",
    )
    is_active: bool = True


class ProductImageUpdate(BaseModel):
    is_main: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductImageUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class ProductImageResponseDTO(ProductImageBase, ORMDTO):
    id: int
    created_at: datetime
