from typing import List, Optional, Union
from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO


# ===================== Translation DTOs =====================


class ProductApplicationTranslationBase(BaseModel):
    locale: Language
    name: str = Field(..., min_length=1, max_length=255)


class ProductApplicationTranslationCreate(ProductApplicationTranslationBase):
    pass


class ProductApplicationTranslationInsert(ProductApplicationTranslationBase):
    application_id: int


class ProductApplicationTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class ProductApplicationTranslationResponseDTO(ProductApplicationTranslationBase, ORMDTO):
    id: int
    application_id: int


# ===================== Application DTOs =====================


class ProductApplicationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unique code, e.g. winch, sheet, halyard")
    index: int = Field(0, ge=0, description="Display order index")
    is_active: bool = Field(True, description="Active status")


class ProductApplicationCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unique code, e.g. winch, sheet, halyard")
    index: Optional[int] = Field(None, ge=0, description="Display order index (auto-generated if omitted)")
    is_active: bool = Field(True, description="Active status")
    translations: List[ProductApplicationTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required when creating an application",
    )


class ProductApplicationUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class ProductApplicationUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


# ===================== Response DTOs =====================


class ProductApplicationResponseDTO(ProductApplicationBase, ORMDTO):
    id: int
    translations: List[ProductApplicationTranslationResponseDTO] = []


class ProductApplicationLocalizedResponseDTO(ORMDTO):
    id: int
    code: str
    index: int
    is_active: bool
    name: str


# ===================== Product Assignment DTOs =====================


class AssignApplicationToProductDTO(BaseModel):
    application_id: int = Field(..., gt=0, description="Application ID to assign to product")


class ProductAssignedApplicationResponseDTO(ORMDTO):
    product_id: int
    application_id: int
    application: Optional[Union[ProductApplicationResponseDTO, ProductApplicationLocalizedResponseDTO]] = None
