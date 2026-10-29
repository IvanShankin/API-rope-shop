from typing import Optional
from pydantic import BaseModel
from src.modules.base.database_model import Language
from src.modules.splice_types.models import SpliceCategory, SpliceVisualType


class CreateSpliceTypeFixtureDTO(BaseModel):
    code: Optional[str] = None
    category: Optional[SpliceCategory] = None
    visual_type: Optional[SpliceVisualType] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    locale: Optional[Language] = None


class CreateSpliceTypeTranslationFixtureDTO(BaseModel):
    splice_type_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
    description: Optional[str] = None
