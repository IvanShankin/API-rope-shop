from typing import Optional

from pydantic import BaseModel

from src.modules.base.database_model import Language


class CreateContentBlockFixtureDTO(BaseModel):
    page_code: Optional[str] = None
    block_code: Optional[str] = None
    is_active: Optional[bool] = None
    locale: Optional[Language] = None
    title: Optional[str] = None
    content: Optional[str] = None


class CreateContentBlockTranslationFixtureDTO(BaseModel):
    content_block_id: Optional[int] = None
    locale: Optional[Language] = None
    title: Optional[str] = None
    content: Optional[str] = None
