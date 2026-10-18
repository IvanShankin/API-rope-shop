from typing import Optional
from pydantic import BaseModel
from src.modules.base.database_model import Language


class CreateProductApplicationFixtureDTO(BaseModel):
    code: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    locale: Optional[Language] = None


class CreateProductApplicationTranslationFixtureDTO(BaseModel):
    application_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None


class CreateProductAssignedApplicationFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    application_id: Optional[int] = None
