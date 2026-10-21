from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from src.core.rate_limit import limiter

from src.modules.base.database_model import Language
from src.modules.check_permission.depends import get_current_admin
from src.modules.reviews.depends import (
    get_optional_admin,
    get_review_service,
)
from src.modules.reviews.models import ReviewsStatus
from src.modules.reviews.models_dto import (
    ReviewCreate,
    ReviewListResponseDTO,
    ReviewResponseDTO,
    ReviewStatusUpdate,
    ReviewTranslationCreate,
    ReviewTranslationResponseDTO,
    ReviewTranslationUpdate,
    ReviewUpdate,
    ReviewUpdateIndexDTO,
)
from src.modules.reviews.service import ReviewService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ============================================================================
# Public & Hybrid Read Endpoints
# ============================================================================


@router.get(
    "",
    response_model=ReviewListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get all reviews",
    description=(
        "Get paginated list of reviews with localized text. "
        "Public/unauthorized users can only see confirmed & published reviews. "
        "Admin can filter by any status, publication state, rating, or search query."
    ),
)
async def get_all_reviews(
    locale: Optional[Language] = Query(
        None, description="Preferred language for translation"
    ),
    status: Optional[ReviewsStatus] = Query(
        None, description="Filter by status (admin only)"
    ),
    is_published: Optional[bool] = Query(
        None, description="Filter by publication status (admin only)"
    ),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by rating (1-5)"),
    search: Optional[str] = Query(
        None, description="Search by author name or review text"
    ),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, description="Pagination limit"),
    service: ReviewService = Depends(get_review_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> ReviewListResponseDTO:
    is_admin = admin is not None
    return await service.get_all_reviews(
        locale=locale,
        status=status,
        is_published=is_published,
        rating=rating,
        search=search,
        skip=skip,
        limit=limit,
        is_admin=is_admin,
    )


@router.get(
    "/{review_id}",
    response_model=ReviewResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get review by ID",
    description=(
        "Get review details by ID with all translations. "
        "Public users can only view confirmed & published reviews."
    ),
)
async def get_review_by_id(
    review_id: int,
    service: ReviewService = Depends(get_review_service),
    admin: Optional[UserDTO] = Depends(get_optional_admin),
) -> ReviewResponseDTO:
    is_admin = admin is not None
    return await service.get_review_by_id(review_id=review_id, is_admin=is_admin)


@router.post(
    "",
    response_model=ReviewResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create review",
    description="Submit a new review with author name, rating, language and text (public). Created with status 'new'.",
)
@limiter.limit("5/minute")
async def create_review(
    request: Request,
    data: ReviewCreate,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponseDTO:
    return await service.create_review(data=data)


# ============================================================================
# Admin Endpoints: Reviews Management
# ============================================================================


@router.patch(
    "/{review_id}",
    response_model=ReviewResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update review attributes",
    description="Update review author, rating, publication status, or review status (admin only).",
)
async def update_review(
    review_id: int,
    data: ReviewUpdate,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ReviewResponseDTO:
    return await service.update_review(review_id=review_id, data=data)


@router.patch(
    "/{review_id}/status",
    response_model=ReviewResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update review status",
    description="Update review moderation status (new, confirmed, rejected) and publication status (admin only).",
)
async def update_review_status(
    review_id: int,
    data: ReviewStatusUpdate,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ReviewResponseDTO:
    return await service.update_review_status(review_id=review_id, data=data)


@router.patch(
    "/{review_id}/index",
    response_model=ReviewResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Reorder review",
    description="Update review position index with automatic neighbor shifting (admin only).",
)
async def reorder_review(
    review_id: int,
    data: ReviewUpdateIndexDTO,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ReviewResponseDTO:
    return await service.reorder_review(review_id=review_id, data=data)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review",
    description="Delete review and its translations (admin only).",
)
async def delete_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_review(review_id=review_id)


# ============================================================================
# Admin Endpoints: Translations Management
# ============================================================================


@router.post(
    "/{review_id}/translations",
    response_model=ReviewTranslationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add review translation",
    description="Add a new language translation for an existing review (admin only).",
)
async def add_review_translation(
    review_id: int,
    data: ReviewTranslationCreate,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ReviewTranslationResponseDTO:
    return await service.add_translation(review_id=review_id, data=data)


@router.patch(
    "/{review_id}/translations/{translation_id}",
    response_model=ReviewTranslationResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update review translation",
    description="Update text of a specific review translation (admin only).",
)
async def update_review_translation(
    review_id: int,
    translation_id: int,
    data: ReviewTranslationUpdate,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> ReviewTranslationResponseDTO:
    return await service.update_translation(
        review_id=review_id,
        translation_id=translation_id,
        data=data,
    )


@router.delete(
    "/{review_id}/translations/{translation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review translation",
    description="Delete a translation of a review. Cannot delete the last remaining translation (admin only).",
)
async def delete_review_translation(
    review_id: int,
    translation_id: int,
    service: ReviewService = Depends(get_review_service),
    admin: UserDTO = Depends(get_current_admin),
) -> None:
    await service.delete_translation(
        review_id=review_id,
        translation_id=translation_id,
    )
