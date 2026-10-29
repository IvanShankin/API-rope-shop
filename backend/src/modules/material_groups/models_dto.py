from typing import List, Optional
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language


class MaterialGroupTranslationBase(BaseModel):
    locale: Language
    name: str


class MaterialGroupTranslationCreate(MaterialGroupTranslationBase):
    pass


class MaterialGroupTranslationInsert(MaterialGroupTranslationCreate):
    material_group_id: int


class MaterialGroupTranslationUpdate(BaseModel):
    name: Optional[str] = None


class MaterialGroupTranslationResponseDTO(MaterialGroupTranslationBase, ORMDTO):
    id: int
    material_group_id: int


class MaterialGroupBase(BaseModel):
    code: str
    index: int
    is_active: bool = True


class MaterialGroupCreate(BaseModel):
    code: str
    index: Optional[int] = Field(None, ge=0, description="Optional index; if not provided, max_index + 1 will be used")
    is_active: bool = True
    translations: List[MaterialGroupTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating a MaterialGroup",
    )


class MaterialGroupUpdate(BaseModel):
    code: Optional[str] = None
    is_active: Optional[bool] = None


class MaterialGroupUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class MaterialGroupResponseDTO(MaterialGroupBase, ORMDTO):
    id: int
    translations: List[MaterialGroupTranslationResponseDTO] = []


class MaterialGroupLocalizedResponseDTO(MaterialGroupBase, ORMDTO):
    id: int
    name: str
