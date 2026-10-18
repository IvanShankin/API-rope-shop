from typing import List, Optional
from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO


# ===================== Translation DTOs =====================


class ProductSpecificationTranslationBase(BaseModel):
    locale: Language
    name: str = Field(..., min_length=1, max_length=255)
    value: str = Field(..., min_length=1, max_length=500)


class ProductSpecificationTranslationCreate(ProductSpecificationTranslationBase):
    pass


class ProductSpecificationTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    value: Optional[str] = Field(None, min_length=1, max_length=500)


class ProductSpecificationTranslationResponseDTO(ProductSpecificationTranslationBase, ORMDTO):
    id: int
    specification_id: int


# ===================== Specification Item DTOs =====================


class ProductSpecificationItemCreate(BaseModel):
    index: Optional[int] = Field(
        None,
        ge=0,
        description="Display order index (auto-generated if omitted)",
    )
    translations: List[ProductSpecificationTranslationCreate] = Field(
        ...,
        min_length=1,
        description="At least one translation is required",
    )


class ProductSpecificationCreate(ProductSpecificationItemCreate):
    product_id: int = Field(..., gt=0, description="Product ID this specification belongs to")


class ProductSpecificationUpdate(BaseModel):
    index: Optional[int] = Field(None, ge=0)
    translations: Optional[List[ProductSpecificationTranslationCreate]] = None


class ProductSpecificationUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


# ===================== Batch DTOs =====================


class ProductSpecificationBatchCreate(BaseModel):
    items: List[ProductSpecificationItemCreate] = Field(
        ...,
        min_length=1,
        description="List of specifications to create for the specified product",
    )


class ProductSpecificationBatchUpdateItem(BaseModel):
    id: int = Field(..., gt=0, description="ID of the specification to update")
    index: Optional[int] = Field(None, ge=0)
    translations: Optional[List[ProductSpecificationTranslationCreate]] = None


class ProductSpecificationBatchUpdate(BaseModel):
    items: List[ProductSpecificationBatchUpdateItem] = Field(
        ...,
        min_length=1,
        description="List of specifications to update for the specified product",
    )


class ProductSpecificationBatchDelete(BaseModel):
    specification_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of specification IDs to delete for the specified product",
    )


class ProductSpecificationBatchSyncItem(BaseModel):
    id: Optional[int] = Field(
        None,
        description="Existing specification ID if updating; omitted/null if creating new",
    )
    index: Optional[int] = Field(None, ge=0)
    translations: List[ProductSpecificationTranslationCreate] = Field(
        ...,
        min_length=1,
        description="Translations for the specification",
    )


class ProductSpecificationBatchSync(BaseModel):
    items: List[ProductSpecificationBatchSyncItem] = Field(
        ...,
        description="Full list of specifications to synchronize for the specified product",
    )


# ===================== Response DTOs =====================


class ProductSpecificationResponseDTO(ORMDTO):
    id: int
    product_id: int
    index: int
    name: Optional[str] = Field(None, description="Localized name when locale requested")
    value: Optional[str] = Field(None, description="Localized value when locale requested")
    translations: List[ProductSpecificationTranslationResponseDTO] = []


class ProductSpecificationLocalizedResponseDTO(ORMDTO):
    id: int
    product_id: int
    index: int
    name: str
    value: str


class ProductSpecificationBatchDeleteResponseDTO(BaseModel):
    deleted_count: int
    deleted_ids: List[int]
