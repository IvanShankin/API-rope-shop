from typing import Optional
from pydantic import BaseModel

from src.modules.base.database_model import Language


class CreateMaterialFixtureDTO(BaseModel):
    material_group_id: Optional[int] = None
    code: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    locale: Optional[Language] = None
    name: Optional[str] = None


class CreateMaterialTranslationFixtureDTO(BaseModel):
    material_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
