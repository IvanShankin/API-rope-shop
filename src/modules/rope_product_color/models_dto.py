from typing import Optional
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.colors.models_dto import ColorResponseDTO, ColorLocalizedResponseDTO


class ProductColorBase(BaseModel):
    product_id: int
    color_id: int
    index: int = 0


class ProductColorCreate(BaseModel):
    product_id: int
    color_id: int


class ProductColorUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class ProductColorResponseDTO(ProductColorBase, ORMDTO):
    id: int
    color: Optional[ColorResponseDTO] = None


class ProductColorLocalizedResponseDTO(ProductColorBase, ORMDTO):
    id: int
    color: Optional[ColorLocalizedResponseDTO] = None
