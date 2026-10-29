from typing import Optional
from pydantic import BaseModel
from src.modules.base.database_model import Language


class CreateProductFixtureDTO(BaseModel):
    category_id: Optional[int] = None
    slug: Optional[str] = None
    product_type: Optional[str] = None
    price_unit: Optional[str] = None
    has_configurator: Optional[bool] = None
    construction_type: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    locale: Optional[Language] = None


class CreateProductTranslationFixtureDTO(BaseModel):
    product_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
