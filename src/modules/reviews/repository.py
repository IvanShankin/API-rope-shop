from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.reviews.models import Review, ReviewsStatus, ReviewTranslation
from src.modules.reviews.models_dto import (
    ReviewBase,
    ReviewTranslationInsert,
)


class ReviewRepository(BaseIndexedRepository):
    """Репозиторий для отзывов (Review)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Review)

    def add_review(self, data: Union[ReviewBase, dict, Any]) -> Review:
        """Добавление отзыва."""
        return self.add(data)

    async def get_by_id(self, review_id: int) -> Optional[Review]:
        """Получение отзыва по ID с предзагрузкой переводов."""
        stmt = (
            select(Review)
            .where(Review.id == review_id)
            .options(selectinload(Review.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        status: Optional[ReviewsStatus] = None,
        is_published: Optional[bool] = None,
        rating: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[Review]:
        """Получение списка отзывов с фильтрацией, поиском и пагинацией."""
        stmt = (
            select(Review)
            .options(selectinload(Review.translations))
            .order_by(Review.index.asc(), Review.id.asc())
        )

        if status is not None:
            stmt = stmt.where(Review.status == status)

        if is_published is not None:
            stmt = stmt.where(Review.is_published == is_published)

        if rating is not None:
            stmt = stmt.where(Review.rating == rating)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Review.author_name.ilike(search_pattern),
                    Review.translations.any(ReviewTranslation.text.ilike(search_pattern)),
                )
            )

        if skip:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_all(
        self,
        status: Optional[ReviewsStatus] = None,
        is_published: Optional[bool] = None,
        rating: Optional[int] = None,
        search: Optional[str] = None,
    ) -> int:
        """Подсчет количества отзывов с учетом фильтров."""
        stmt = select(func.count(Review.id))

        if status is not None:
            stmt = stmt.where(Review.status == status)

        if is_published is not None:
            stmt = stmt.where(Review.is_published == is_published)

        if rating is not None:
            stmt = stmt.where(Review.rating == rating)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Review.author_name.ilike(search_pattern),
                    Review.translations.any(ReviewTranslation.text.ilike(search_pattern)),
                )
            )

        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def update_review(self, review_id: int, update_data: dict) -> None:
        """Обновление атрибутов отзыва."""
        stmt = update(Review).where(Review.id == review_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_review(self, review_id: int) -> None:
        """Удаление отзыва."""
        stmt = delete(Review).where(Review.id == review_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, review_id: int) -> bool:
        """Проверка зависимостей (у отзыва нет внешних ссылок из других таблиц)."""
        return False


class ReviewTranslationRepository(BaseRepository):
    """Репозиторий для переводов отзывов (ReviewTranslation)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ReviewTranslation)

    def add_translation(
        self, data: Union[ReviewTranslationInsert, dict, Any]
    ) -> ReviewTranslation:
        """Добавление перевода."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> Optional[ReviewTranslation]:
        """Получение перевода по ID."""
        stmt = select(ReviewTranslation).where(ReviewTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_review_and_locale(
        self, review_id: int, locale: Language
    ) -> Optional[ReviewTranslation]:
        """Получение перевода по review_id и локали."""
        stmt = select(ReviewTranslation).where(
            ReviewTranslation.review_id == review_id,
            ReviewTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода."""
        stmt = (
            update(ReviewTranslation)
            .where(ReviewTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода."""
        stmt = delete(ReviewTranslation).where(ReviewTranslation.id == translation_id)
        await self.session.execute(stmt)

    async def count_by_review_id(self, review_id: int) -> int:
        """Подсчет количества переводов для отзыва."""
        stmt = select(func.count(ReviewTranslation.id)).where(
            ReviewTranslation.review_id == review_id
        )
        result = await self.session.scalar(stmt)
        return int(result or 0)
