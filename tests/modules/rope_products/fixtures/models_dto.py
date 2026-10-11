from typing import Optional
from pydantic import BaseModel


class CreateRopeProductFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    material_group_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    working_stretch_percent: Optional[float] = None
    can_be_spliced: Optional[bool] = None


class CreateRopeVariantFixtureDTO(BaseModel):
    rope_product_id: Optional[int] = None
    diameter_mm: Optional[float] = None
    breaking_load_dan: Optional[float] = None
    weight_g_per_m: Optional[float] = None
    price_per_meter: Optional[float] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
