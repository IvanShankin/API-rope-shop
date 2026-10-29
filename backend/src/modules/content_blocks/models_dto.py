from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO


class ContentBlockTranslationUpsertDTO(BaseModel):
    locale: Language = Field(..., description="Translation language code")
    title: Optional[str] = Field(None, max_length=500, description="Block title")
    content: Optional[str] = Field(None, description="Block text/HTML/markdown content")


class ContentBlockTranslationResponseDTO(ORMDTO):
    id: int
    content_block_id: int
    locale: Language
    title: Optional[str] = None
    content: Optional[str] = None


class ContentBlockBaseDTO(BaseModel):
    page_code: str = Field(
        ..., min_length=1, max_length=100, description="Page identifier"
    )
    block_code: str = Field(
        ..., min_length=1, max_length=100, description="Block identifier within page"
    )
    index: int = Field(0, description="Sorting index")
    is_active: bool = Field(True, description="Active status")


class ContentBlockCreateDTO(ContentBlockBaseDTO):
    translations: List[ContentBlockTranslationUpsertDTO] = Field(
        default_factory=list, description="Initial translations for the block"
    )


class ContentBlockUpdateDTO(BaseModel):
    page_code: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Page identifier"
    )
    index: Optional[int] = Field(
        None, description="Sorting index"
    )
    is_active: Optional[bool] = Field(
        None, description="Active status of the content block"
    )
    translations: Optional[List[ContentBlockTranslationUpsertDTO]] = Field(
        None,
        description="Batch of translations to update or insert for this block",
    )


class ContentBlockResponseDTO(ContentBlockBaseDTO, ORMDTO):
    id: int
    title: Optional[str] = Field(
        None, description="Localized block title according to requested locale/fallback"
    )
    content: Optional[str] = Field(
        None,
        description="Localized block content according to requested locale/fallback",
    )
    locale: Optional[Language] = Field(
        None, description="Matched locale for title/content"
    )
    translations: List[ContentBlockTranslationResponseDTO] = Field(
        default_factory=list,
        description="Always loaded full list of translations for this block",
    )
    created_at: datetime
    updated_at: datetime
