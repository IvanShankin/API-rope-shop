from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from src.modules.base.database_model import Language
from src.modules.reviews.models import Review, ReviewsStatus, ReviewTranslation
from src.modules.reviews.models_dto import (
    ReviewResponseDTO,
    ReviewTranslationResponseDTO,
)
from tests.helpers.functions import random_string
from tests.modules.reviews.fixtures.models_dto import (
    CreateReviewFixtureDTO,
    CreateReviewTranslationFixtureDTO,
)


async def create_review_factory(
    session_db: AsyncSession,
    new_review: CreateReviewFixtureDTO = CreateReviewFixtureDTO(),
) -> ReviewResponseDTO:
    author_name = (
        new_review.author_name
        if new_review.author_name is not None
        else f"Author {random_string(6)}"
    )
    rating = new_review.rating if new_review.rating is not None else 5
    is_published = (
        new_review.is_published if new_review.is_published is not None else True
    )
    status = (
        new_review.status
        if new_review.status is not None
        else ReviewsStatus.CONFIRMED
    )
    index = new_review.index if new_review.index is not None else 0
    locale = new_review.locale if new_review.locale is not None else Language.ENG
    text = (
        new_review.text
        if new_review.text is not None
        else f"Great rope quality! {random_string(10)}"
    )

    review = Review(
        author_name=author_name,
        rating=rating,
        is_published=is_published,
        status=status,
        index=index,
    )
    session_db.add(review)
    await session_db.flush()

    translation = ReviewTranslation(
        review_id=review.id,
        locale=locale,
        text=text,
    )
    session_db.add(translation)
    await session_db.commit()

    stmt = (
        select(Review)
        .where(Review.id == review.id)
        .options(selectinload(Review.translations))
    )
    result = await session_db.execute(stmt)
    loaded = result.scalar_one()

    return ReviewResponseDTO.model_validate(loaded)


async def create_review_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateReviewTranslationFixtureDTO = CreateReviewTranslationFixtureDTO(),
) -> ReviewTranslationResponseDTO:
    if new_trans.review_id is None:
        rev_dto = await create_review_factory(session_db=session_db)
        review_id = rev_dto.id
    else:
        review_id = new_trans.review_id

    locale = new_trans.locale if new_trans.locale is not None else Language.GER
    text = (
        new_trans.text
        if new_trans.text is not None
        else f"Translated review text {random_string(8)}"
    )

    translation = ReviewTranslation(
        review_id=review_id,
        locale=locale,
        text=text,
    )
    session_db.add(translation)
    await session_db.commit()
    await session_db.refresh(translation)

    return ReviewTranslationResponseDTO.model_validate(translation)
