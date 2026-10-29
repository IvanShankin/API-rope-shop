from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.rope_product_color.models_dto import ProductColorResponseDTO
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceResponseDTO
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO


# ===================== ProductVariant DTOs =====================

class ProductVariantBase(BaseModel):
    product_id: int
    variant_name: str
    size_value: Optional[float] = None
    breaking_load_dan: Optional[float] = None
    working_load_dan: Optional[float] = None
    working_stretch_percent: Optional[float] = None
    weight_g: Optional[float] = None
    price: float
    sku: Optional[str] = None
    index: int = 0
    is_active: bool = True


class ProductVariantCreate(BaseModel):
    product_id: int
    variant_name: str = Field(..., max_length=100, description="Variant name (e.g. '8 мм', '70 мм / M8')")
    size_value: Optional[float] = Field(None, gt=0, description="Size/diameter value (e.g. 8.0)")
    breaking_load_dan: Optional[float] = Field(None, ge=0, description="Breaking load in daN")
    working_load_dan: Optional[float] = Field(None, ge=0, description="Working load in daN")
    working_stretch_percent: Optional[float] = Field(None, ge=0, description="Working stretch percent")
    weight_g: Optional[float] = Field(None, ge=0, description="Weight in g")
    price: float = Field(..., ge=0, description="Price (>= 0)")
    sku: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class ProductVariantCreateForProduct(BaseModel):
    variant_name: str = Field(..., max_length=100, description="Variant name (e.g. '8 мм')")
    size_value: Optional[float] = Field(None, gt=0, description="Size/diameter value (e.g. 8.0)")
    breaking_load_dan: Optional[float] = Field(None, ge=0, description="Breaking load in daN")
    working_load_dan: Optional[float] = Field(None, ge=0, description="Working load in daN")
    working_stretch_percent: Optional[float] = Field(None, ge=0, description="Working stretch percent")
    weight_g: Optional[float] = Field(None, ge=0, description="Weight in g")
    price: float = Field(..., ge=0, description="Price (>= 0)")
    sku: Optional[str] = Field(None, max_length=100)
    is_active: bool = True


class ProductVariantUpdate(BaseModel):
    variant_name: Optional[str] = Field(None, max_length=100)
    size_value: Optional[float] = Field(None, gt=0)
    breaking_load_dan: Optional[float] = Field(None, ge=0)
    working_load_dan: Optional[float] = Field(None, ge=0)
    working_stretch_percent: Optional[float] = Field(None, ge=0)
    weight_g: Optional[float] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    sku: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductVariantUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class ProductVariantResponseDTO(ProductVariantBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime


# ===================== RopeConfiguratorSetting DTOs =====================

class RopeConfiguratorSettingBase(BaseModel):
    product_id: Optional[int] = None
    material_group_id: int
    material_id: Optional[int] = None
    splice_material_id: int
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    can_be_spliced: bool = True


class RopeConfiguratorSettingCreate(RopeConfiguratorSettingBase):
    product_id: int = Field(
        ...,
        description="Base product ID for which configurator settings are defined."
    )


class RopeConfiguratorSettingUpdate(BaseModel):
    material_group_id: Optional[int] = None
    material_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    can_be_spliced: Optional[bool] = None


class RopeConfiguratorSettingResponseDTO(RopeConfiguratorSettingBase, ORMDTO):
    product_id: int
    created_at: datetime
    updated_at: datetime


class RopeConfiguratorSettingDetailResponseDTO(RopeConfiguratorSettingResponseDTO):
    variants: List[ProductVariantResponseDTO] = []
    colors: List[ProductColorResponseDTO] = []
    allowed_splices: List[RopeAllowedSpliceResponseDTO] = []
    splice_material: Optional[SpliceMaterialResponseDTO] = None
