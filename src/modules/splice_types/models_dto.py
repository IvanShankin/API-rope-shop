from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.database_model import Language
from src.modules.splice_types.models import SpliceCategory, SpliceVisualType

class SpliceTypeTranslationBase(BaseModel):
    locale: Language
    name: str
    description: Optional[str] = None

class SpliceTypeTranslationCreate(SpliceTypeTranslationBase):
    pass

class SpliceTypeTranslationInsert(SpliceTypeTranslationCreate):
    splice_type_id: int

class SpliceTypeTranslationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class SpliceTypeTranslationResponseDTO(SpliceTypeTranslationBase, ORMDTO):
    id: int
    splice_type_id: int

class SpliceTypeBase(BaseModel):
    code: str
    category: SpliceCategory
    visual_type: SpliceVisualType
    image_url: Optional[str] = None
    index: int
    is_active: bool = True

class SpliceTypeCreate(BaseModel):
    code: str
    category: SpliceCategory
    visual_type: SpliceVisualType
    index: int
    is_active: bool = True
    translations: List[SpliceTypeTranslationCreate]

class SpliceTypeUpdate(BaseModel):
    code: Optional[str] = None
    category: Optional[SpliceCategory] = None
    visual_type: Optional[SpliceVisualType] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None

class SpliceTypeResponseDTO(SpliceTypeBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    translations: List[SpliceTypeTranslationResponseDTO] = []
    
class SpliceTypeLocalizedResponseDTO(SpliceTypeBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    name: str
    description: Optional[str] = None


# ==================== Dependencies DTOs ====================

class SplicePriceRuleDependencyDTO(BaseModel):
    id: int
    splice_material_id: int
    diameter_from_mm: float
    diameter_to_mm: float
    price: float


class RopeDependencyDTO(BaseModel):
    product_id: int
    name: Optional[str] = None


class SpliceTypeDependenciesDTO(BaseModel):
    has_dependencies: bool
    can_delete: bool
    rules_count: int
    ropes_count: int
    rules: List[SplicePriceRuleDependencyDTO] = []
    ropes: List[RopeDependencyDTO] = []
