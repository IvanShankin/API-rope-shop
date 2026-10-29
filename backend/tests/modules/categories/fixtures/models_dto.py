from typing import Optional
from pydantic import BaseModel
from src.modules.base.database_model import Language


class CreateCategoryFixtureDTO(BaseModel):
    slug: Optional[str] = None
    image_url: Optional[str] = None
    index: Optional[int] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    locale: Optional[Language] = None


class CreateCategoryTranslationFixtureDTO(BaseModel):
    category_id: Optional[int] = None
    locale: Optional[Language] = None
    name: Optional[str] = None
