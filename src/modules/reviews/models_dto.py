from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.modules.base.database_model import Language
from src.modules.base.orm_dto import ORMDTO
from src.modules.reviews.models import ReviewsStatus


# ==================== Translation DTOs ====================


class ReviewTranslationCreate(BaseModel):
    locale: Language = Field(..., description="Language code for the translation")
    text: str = Field(..., min_length=1, description="Translated review text")


class ReviewTranslationUpdate(BaseModel):
    text: str = Field(..., min_length=1, description="Updated review text")


class ReviewTranslationResponseDTO(ORMDTO):
    id: int
    review_id: int
    locale: Language
    text: str


class ReviewTranslationInsert(BaseModel):
    review_id: int
    locale: Language
    text: str


# ==================== Review DTOs ====================


class ReviewBase(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=255)
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    is_published: bool = False
    status: ReviewsStatus = ReviewsStatus.NEW
    index: int = Field(0, ge=0)


class ReviewCreate(BaseModel):
    author_name: str = Field(..., min_length=1, max_length=255, description="Author name")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    locale: Language = Field(..., description="Language in which the review is written")
    text: str = Field(..., min_length=1, description="Review text")


class ReviewUpdate(BaseModel):
    author_name: Optional[str] = Field(None, min_length=1, max_length=255)
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_published: Optional[bool] = None
    status: Optional[ReviewsStatus] = None


class ReviewStatusUpdate(BaseModel):
    status: ReviewsStatus = Field(..., description="New review status")
    is_published: Optional[bool] = Field(
        None, description="Optionally toggle publication status"
    )


class ReviewUpdateIndexDTO(BaseModel):
    new_index: int = Field(..., ge=0, description="New position index (>= 0)")


class ReviewResponseDTO(ReviewBase, ORMDTO):
    id: int
    created_at: datetime
    updated_at: datetime
    translations: List[ReviewTranslationResponseDTO] = []


class ReviewLocalizedResponseDTO(ReviewBase, ORMDTO):
    id: int
    text: Optional[str] = None
    locale: Optional[Language] = None
    translations: List[ReviewTranslationResponseDTO] = []
    created_at: datetime
    updated_at: datetime


class ReviewListResponseDTO(BaseModel):
    items: List[ReviewLocalizedResponseDTO]
    total: int
    skip: int = 0
    limit: Optional[int] = None
