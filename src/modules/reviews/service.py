from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.base.exception import NoDataForUpdate
from src.modules.reviews.exception import (
    ReviewHasDependencies,
    ReviewNotFound,
    ReviewTranslationAlreadyExists,
    ReviewTranslationDeleteError,
    ReviewTranslationNotFound,
)
from src.modules.reviews.models import Review, ReviewsStatus
from src.modules.reviews.models_dto import (
    ReviewBase,
    ReviewCreate,
    ReviewListResponseDTO,
    ReviewLocalizedResponseDTO,
    ReviewResponseDTO,
    ReviewStatusUpdate,
    ReviewTranslationCreate,
    ReviewTranslationInsert,
    ReviewTranslationResponseDTO,
    ReviewTranslationUpdate,
    ReviewUpdate,
    ReviewUpdateIndexDTO,
)
from src.modules.reviews.repository import (
    ReviewRepository,
    ReviewTranslationRepository,
)


class ReviewService:
    def __init__(
        self,
        review_repo: ReviewRepository,
        translation_repo: ReviewTranslationRepository,
        session: AsyncSession,
    ):
        self.review_repo = review_repo
        self.translation_repo = translation_repo
        self.session = session

    async def create_review(self, data: ReviewCreate) -> ReviewResponseDTO:
        """
        Создание нового отзыва с начальным переводом.
        Доступно публично любому пользователю.
        Новый отзыв всегда создается со статусом NEW и is_published=False.
        """
        count = await self.review_repo.count_all()
        max_index = await self.review_repo.get_max_index()
        target_index = 0 if count == 0 else max_index + 1

        review_base = ReviewBase(
            author_name=data.author_name,
            rating=data.rating,
            is_published=False,
            status=ReviewsStatus.NEW,
            index=target_index,
        )
        new_review = self.review_repo.add_review(review_base)
        await self.session.flush()

        insert_translation = ReviewTranslationInsert(
            review_id=new_review.id,
            locale=data.locale,
            text=data.text,
        )
        self.translation_repo.add_translation(insert_translation)
        await self.session.commit()

        loaded = await self.review_repo.get_by_id(new_review.id)
        return ReviewResponseDTO.model_validate(loaded)

    async def get_all_reviews(
        self,
        locale: Optional[Language] = None,
        status: Optional[ReviewsStatus] = None,
        is_published: Optional[bool] = None,
        rating: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
        is_admin: bool = False,
    ) -> ReviewListResponseDTO:
        """
        Получение списка отзывов с фильтрацией, пагинацией и локализацией.
        Обычные (неавторизованные или не-админы) пользователи могут просматривать
        только отзывы со статусом CONFIRMED (и is_published=True).
        Администратор может просматривать отзывы в любых статусах.
        """
        effective_status = status
        effective_published = is_published

        if not is_admin:
            effective_status = ReviewsStatus.CONFIRMED
            effective_published = True

        reviews = await self.review_repo.get_all(
            status=effective_status,
            is_published=effective_published,
            rating=rating,
            search=search,
            skip=skip,
            limit=limit,
        )
        total = await self.review_repo.count_all(
            status=effective_status,
            is_published=effective_published,
            rating=rating,
            search=search,
        )

        items = [self._to_localized_dto(r, locale) for r in reviews]
        return ReviewListResponseDTO(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_review_by_id(
        self,
        review_id: int,
        is_admin: bool = False,
    ) -> ReviewResponseDTO:
        """
        Получение детальной информации об отзыве по ID со всеми его переводами.
        Обычные пользователи могут получить только подтвержденный и опубликованный отзыв.
        """
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        if not is_admin and (
            review.status != ReviewsStatus.CONFIRMED or not review.is_published
        ):
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        return ReviewResponseDTO.model_validate(review)

    async def update_review(
        self,
        review_id: int,
        data: ReviewUpdate,
    ) -> ReviewResponseDTO:
        """Обновление атрибутов отзыва (только админ)."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("No data provided for update.")

        await self.review_repo.update_review(review_id, update_dict)
        await self.session.commit()

        updated = await self.review_repo.get_by_id(review_id)
        return ReviewResponseDTO.model_validate(updated)

    async def update_review_status(
        self,
        review_id: int,
        data: ReviewStatusUpdate,
    ) -> ReviewResponseDTO:
        """Изменение статуса и публикации отзыва (только админ)."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        update_dict = data.model_dump(exclude_unset=True)
        await self.review_repo.update_review(review_id, update_dict)
        await self.session.commit()

        updated = await self.review_repo.get_by_id(review_id)
        return ReviewResponseDTO.model_validate(updated)

    async def reorder_review(
        self,
        review_id: int,
        data: ReviewUpdateIndexDTO,
    ) -> ReviewResponseDTO:
        """Перемещение позиции отзыва со сдвигом соседних записей (только админ)."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        if review.index != data.new_index:
            await self.review_repo.reorder_index(
                obj_id=review_id,
                old_index=review.index,
                new_index=data.new_index,
            )
            await self.session.commit()

        updated = await self.review_repo.get_by_id(review_id)
        return ReviewResponseDTO.model_validate(updated)

    async def delete_review(self, review_id: int) -> None:
        """Удаление отзыва со всеми его переводами со сдвигом индексов (только админ)."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        has_deps = await self.review_repo.has_dependencies(review_id)
        if has_deps:
            raise ReviewHasDependencies(
                f"Cannot delete Review {review_id}: it has dependent records."
            )

        deleted_index = review.index
        await self.review_repo.delete_review(review_id)
        await self.review_repo.shift_indexes_after_delete(deleted_index=deleted_index)
        await self.session.commit()

    # ==================== Управление переводами (Админ) ====================

    async def add_translation(
        self,
        review_id: int,
        data: ReviewTranslationCreate,
    ) -> ReviewTranslationResponseDTO:
        """Добавление перевода для существующего отзыва (только админ)."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        existing = await self.translation_repo.get_by_review_and_locale(
            review_id=review_id,
            locale=data.locale,
        )
        if existing:
            raise ReviewTranslationAlreadyExists(
                f"Translation for locale '{data.locale.value}' already exists for review {review_id}."
            )

        insert_dto = ReviewTranslationInsert(
            review_id=review_id,
            locale=data.locale,
            text=data.text,
        )
        trans = self.translation_repo.add_translation(insert_dto)
        await self.session.commit()
        await self.session.refresh(trans)

        return ReviewTranslationResponseDTO.model_validate(trans)

    async def update_translation(
        self,
        review_id: int,
        translation_id: int,
        data: ReviewTranslationUpdate,
    ) -> ReviewTranslationResponseDTO:
        """Обновление текста перевода (только админ)."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans or trans.review_id != review_id:
            raise ReviewTranslationNotFound(
                f"Translation with id {translation_id} for review {review_id} not found."
            )

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("No data provided for update.")

        await self.translation_repo.update_translation(translation_id, update_dict)
        await self.session.commit()

        updated = await self.translation_repo.get_by_id(translation_id)
        return ReviewTranslationResponseDTO.model_validate(updated)

    async def delete_translation(
        self,
        review_id: int,
        translation_id: int,
    ) -> None:
        """
        Удаление перевода отзыва (только админ).
        Запрещено удалять единственный оставшийся перевод сущности (правило 5.1).
        """
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Review with id {review_id} not found.")

        trans = await self.translation_repo.get_by_id(translation_id)
        if not trans or trans.review_id != review_id:
            raise ReviewTranslationNotFound(
                f"Translation with id {translation_id} for review {review_id} not found."
            )

        count = await self.translation_repo.count_by_review_id(review_id)
        if count <= 1:
            raise ReviewTranslationDeleteError(
                "Cannot delete the only remaining translation of the review."
            )

        await self.translation_repo.delete_translation(translation_id)
        await self.session.commit()

    # ==================== Вспомогательные методы ====================

    def _to_localized_dto(
        self,
        review: Review,
        locale: Optional[Language],
    ) -> ReviewLocalizedResponseDTO:
        """Преобразование ORM Review в DTO с локализацией текста по запрошенной локали."""
        target_locale = locale or Language.ENG
        text = review._get_field_with_translation(
            lambda t: t.text,
            target_locale,
            fallback=Language.ENG,
        )

        matched_locale: Optional[Language] = None
        if review.translations:
            target_norm = Review._normalize_locale(target_locale)
            for t in review.translations:
                if Review._normalize_locale(t.locale) == target_norm:
                    matched_locale = t.locale
                    break
            if not matched_locale:
                fallback_norm = Review._normalize_locale(Language.ENG)
                for t in review.translations:
                    if Review._normalize_locale(t.locale) == fallback_norm:
                        matched_locale = t.locale
                        break
            if not matched_locale and review.translations:
                matched_locale = review.translations[0].locale

        return ReviewLocalizedResponseDTO(
            id=review.id,
            author_name=review.author_name,
            rating=review.rating,
            is_published=review.is_published,
            status=review.status,
            index=review.index,
            text=text,
            locale=matched_locale,
            translations=[
                ReviewTranslationResponseDTO.model_validate(t)
                for t in review.translations
            ],
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
