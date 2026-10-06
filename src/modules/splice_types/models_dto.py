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

class SpliceTypeCreate(SpliceTypeBase):
    pass

class SpliceTypeUpdate(BaseModel):
    code: Optional[str] = None
    category: Optional[SpliceCategory] = None
    visual_type: Optional[SpliceVisualType] = None
    image_url: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None

class SpliceTypeResponseDTO(SpliceTypeBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    translations: List[SpliceTypeTranslationResponseDTO] = []
