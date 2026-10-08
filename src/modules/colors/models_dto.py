from typing import List, Optional
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language


class ColorTranslationBase(BaseModel):
    locale: Language
    name: str


class ColorTranslationCreate(ColorTranslationBase):
    pass


class ColorTranslationInsert(ColorTranslationCreate):
    color_id: int


class ColorTranslationUpdate(BaseModel):
    name: Optional[str] = None


class ColorTranslationResponseDTO(ColorTranslationBase, ORMDTO):
    id: int
    color_id: int


class ColorBase(BaseModel):
    code: str
    hex: Optional[str] = None
    index: int
    is_active: bool = True


class ColorCreate(ColorBase):
    translations: List[ColorTranslationCreate]


class ColorUpdate(BaseModel):
    code: Optional[str] = None
    hex: Optional[str] = None
    is_active: Optional[bool] = None


class ColorUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class ColorResponseDTO(ColorBase, ORMDTO):
    id: int
    translations: List[ColorTranslationResponseDTO] = []


class ColorLocalizedResponseDTO(ColorBase, ORMDTO):
    id: int
    name: str
