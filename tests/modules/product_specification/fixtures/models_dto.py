from typing import Optional
from pydantic import BaseModel
from src.modules.base.database_model import Language


class CreateProductSpecificationFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    index: Optional[int] = None
    name: Optional[str] = None
    value: Optional[str] = None
    locale: Optional[Language] = None


class CreateProductSpecificationTranslationFixtureDTO(BaseModel):
    specification_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
    value: Optional[str] = None
