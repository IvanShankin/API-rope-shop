from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from src.modules.base.orm_dto import ORMDTO
from src.modules.splice_types.models_dto import SpliceTypeResponseDTO

class SplicePriceRuleBase(BaseModel):
    splice_type_id: int
    splice_material_id: int
    diameter_from_mm: Optional[float] = None
    diameter_to_mm: Optional[float] = None
    price: float
    is_active: bool = True

class SplicePriceRuleResponseDTO(SplicePriceRuleBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    
class SplicePriceRuleWithRelationsResponseDTO(SplicePriceRuleResponseDTO):
    splice_type: SpliceTypeResponseDTO
