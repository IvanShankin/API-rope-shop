from typing import Optional
from pydantic import BaseModel

class CreateSpliceMaterialFixtureDTO(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
