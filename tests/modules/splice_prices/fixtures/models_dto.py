from typing import Optional
from pydantic import BaseModel

class CreateSplicePriceRuleFixtureDTO(BaseModel):
    splice_type_id: Optional[int] = None
    splice_material_id: Optional[int] = None
    diameter_from_mm: Optional[float] = None
    diameter_to_mm: Optional[float] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None
