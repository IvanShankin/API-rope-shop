from typing import Optional

from pydantic import BaseModel

from src.modules.base.database_model import Language
from src.modules.reviews.models import ReviewsStatus


class CreateReviewFixtureDTO(BaseModel):
    author_name: Optional[str] = None
    rating: Optional[int] = None
    is_published: Optional[bool] = None
    status: Optional[ReviewsStatus] = None
    index: Optional[int] = None
    locale: Optional[Language] = None
    text: Optional[str] = None


class CreateReviewTranslationFixtureDTO(BaseModel):
    review_id: Optional[int] = None
    locale: Optional[Language] = None
    text: Optional[str] = None
