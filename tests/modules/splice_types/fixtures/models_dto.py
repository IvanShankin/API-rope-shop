from typing import Optional
from pydantic import BaseModel
from src.modules.splice_types.models import SpliceCategory, SpliceVisualType

class CreateSpliceTypeFixtureDTO(BaseModel):
    code: Optional[str] = None
    category: Optional[SpliceCategory] = None
    visual_type: Optional[SpliceVisualType] = None
    index: Optional[int] = None
