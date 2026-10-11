from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.rope_product_color.models_dto import RopeProductColorResponseDTO
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceResponseDTO
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO


# ===================== RopeVariant DTOs =====================

class RopeVariantBase(BaseModel):
    rope_product_id: int
    diameter_mm: float
    breaking_load_dan: Optional[float] = None
    weight_g_per_m: Optional[float] = None
    price_per_meter: float
    index: int
    is_active: bool = True


class RopeVariantCreate(BaseModel):
    rope_product_id: int
    diameter_mm: float = Field(..., gt=0, description="Diameter in millimeters (> 0)")
    breaking_load_dan: Optional[float] = Field(None, ge=0, description="Breaking load in daN")
    weight_g_per_m: Optional[float] = Field(None, ge=0, description="Weight in g/m")
    price_per_meter: float = Field(..., ge=0, description="Price per meter (>= 0)")
    is_active: bool = True


class RopeVariantCreateForProduct(BaseModel):
    diameter_mm: float = Field(..., gt=0, description="Diameter in millimeters (> 0)")
    breaking_load_dan: Optional[float] = Field(None, ge=0, description="Breaking load in daN")
    weight_g_per_m: Optional[float] = Field(None, ge=0, description="Weight in g/m")
    price_per_meter: float = Field(..., ge=0, description="Price per meter (>= 0)")
    is_active: bool = True


class RopeVariantUpdate(BaseModel):
    diameter_mm: Optional[float] = Field(None, gt=0, description="Diameter in millimeters (> 0)")
    breaking_load_dan: Optional[float] = Field(None, ge=0, description="Breaking load in daN")
    weight_g_per_m: Optional[float] = Field(None, ge=0, description="Weight in g/m")
    price_per_meter: Optional[float] = Field(None, ge=0, description="Price per meter (>= 0)")
    is_active: Optional[bool] = None


class RopeVariantUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class RopeVariantResponseDTO(RopeVariantBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime


# ===================== RopeProduct DTOs =====================

class RopeProductBase(BaseModel):
    material_group_id: int
    splice_material_id: int
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    working_stretch_percent: Optional[float] = None
    can_be_spliced: bool = True


class RopeProductCreate(RopeProductBase):
    product_id: Optional[int] = Field(
        None,
        description="Optional base product ID. If not provided, a base Product will be created automatically."
    )


class RopeProductUpdate(BaseModel):
    material_group_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    working_stretch_percent: Optional[float] = None
    can_be_spliced: Optional[bool] = None


class RopeProductResponseDTO(RopeProductBase, ORMDTO):
    product_id: int
    created_at: datetime
    updated_at: datetime


class RopeProductDetailResponseDTO(RopeProductResponseDTO):
    variants: List[RopeVariantResponseDTO] = []
    colors: List[RopeProductColorResponseDTO] = []
    allowed_splices: List[RopeAllowedSpliceResponseDTO] = []
    splice_material: Optional[SpliceMaterialResponseDTO] = None
