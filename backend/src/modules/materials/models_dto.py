from typing import List, Optional
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language


class MaterialTranslationBase(BaseModel):
    locale: Language
    name: str


class MaterialTranslationCreate(MaterialTranslationBase):
    pass


class MaterialTranslationInsert(MaterialTranslationCreate):
    material_id: int


class MaterialTranslationUpdate(BaseModel):
    name: Optional[str] = None


class MaterialTranslationResponseDTO(MaterialTranslationBase, ORMDTO):
    id: int
    material_id: int


class MaterialBase(BaseModel):
    material_group_id: int
    code: str
    index: int
    is_active: bool = True


class MaterialCreate(BaseModel):
    material_group_id: int
    code: str
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Optional index; if not provided, max_index + 1 will be used scoped to material_group_id",
    )
    is_active: bool = True
    translations: List[MaterialTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating a Material",
    )


class MaterialUpdate(BaseModel):
    material_group_id: Optional[int] = None
    code: Optional[str] = None
    is_active: Optional[bool] = None


class MaterialUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class MaterialResponseDTO(MaterialBase, ORMDTO):
    id: int
    translations: List[MaterialTranslationResponseDTO] = []


class MaterialLocalizedResponseDTO(MaterialBase, ORMDTO):
    id: int
    name: str
