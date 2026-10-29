from typing import Optional
from pydantic import BaseModel
from src.modules.base.database_model import Language


class CreateColorFixtureDTO(BaseModel):
    code: Optional[str] = None
    hex: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    locale: Optional[Language] = None


class CreateColorTranslationFixtureDTO(BaseModel):
    color_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
