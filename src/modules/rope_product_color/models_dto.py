from typing import Optional
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.colors.models_dto import ColorResponseDTO, ColorLocalizedResponseDTO


class RopeProductColorBase(BaseModel):
    rope_product_id: int
    color_id: int
    index: int


class RopeProductColorCreate(BaseModel):
    rope_product_id: int
    color_id: int


class RopeProductColorUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class RopeProductColorResponseDTO(RopeProductColorBase, ORMDTO):
    id: int
    color: Optional[ColorResponseDTO] = None


class RopeProductColorLocalizedResponseDTO(RopeProductColorBase, ORMDTO):
    id: int
    color: Optional[ColorLocalizedResponseDTO] = None
