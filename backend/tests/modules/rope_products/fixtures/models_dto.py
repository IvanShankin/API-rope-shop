from typing import Optional
from pydantic import BaseModel


class CreateRopeProductFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    material_group_id: Optional[int] = None
    material_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    construction: Optional[str] = None
    core_description: Optional[str] = None
    cover_description: Optional[str] = None
    can_be_spliced: Optional[bool] = None


class CreateRopeVariantFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    variant_name: Optional[str] = None
    size_value: Optional[float] = None
    breaking_load_dan: Optional[float] = None
    working_load_dan: Optional[float] = None
    working_stretch_percent: Optional[float] = None
    weight_g: Optional[float] = None
    price: Optional[float] = None
    sku: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
