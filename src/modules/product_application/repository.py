from typing import Any, Optional, Sequence, Union
from sqlalchemy import delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseIndexedRepository, BaseRepository
from src.modules.product_application.models import (
    ProductApplication,
    ProductApplicationTranslation,
    ProductAssignedApplication,
)
from src.modules.product_application.models_dto import ProductApplicationTranslationInsert


class ProductApplicationRepository(BaseIndexedRepository):
    """Репозиторий для справочника назначений товаров (ProductApplication)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductApplication)

    async def add_application(self, code: str, index: int, is_active: bool = True) -> ProductApplication:
        """Добавление нового назначения."""
        app = ProductApplication(code=code, index=index, is_active=is_active)
        self.session.add(app)
        return app

    async def get_by_id(self, app_id: int) -> Optional[ProductApplication]:
        """Получение назначения по ID с предзагрузкой переводов."""
        stmt = (
            select(ProductApplication)
            .where(ProductApplication.id == app_id)
            .options(selectinload(ProductApplication.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[ProductApplication]:
        """Получение назначения по коду с предзагрузкой переводов."""
        stmt = (
            select(ProductApplication)
            .where(ProductApplication.code == code)
            .options(selectinload(ProductApplication.translations))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Sequence[ProductApplication]:
        """Получение всех назначений, отсортированных по index."""
        stmt = (
            select(ProductApplication)
            .options(selectinload(ProductApplication.translations))
            .order_by(ProductApplication.index.asc(), ProductApplication.id.asc())
        )
        if is_active is not None:
            stmt = stmt.where(ProductApplication.is_active == is_active)
        if skip:
            stmt = stmt.offset(skip)
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, is_active: Optional[bool] = None) -> int:
        """Подсчет количества назначений."""
        stmt = select(func.count(ProductApplication.id))
        if is_active is not None:
            stmt = stmt.where(ProductApplication.is_active == is_active)
        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def exists_code(self, code: str) -> bool:
        """Проверка существования назначения с данным кодом."""
        stmt = select(exists().where(ProductApplication.code == code))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def has_dependencies(self, app_id: int) -> bool:
        """Проверка, привязано ли назначение к каким-либо товарам."""
        stmt = select(exists().where(ProductAssignedApplication.application_id == app_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def update_application(self, app_id: int, update_data: dict) -> None:
        """Обновление назначения по ID."""
        stmt = (
            update(ProductApplication)
            .where(ProductApplication.id == app_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_application(self, app_id: int) -> None:
        """Удаление назначения по ID."""
        stmt = delete(ProductApplication).where(ProductApplication.id == app_id)
        await self.session.execute(stmt)


class ProductApplicationTranslationRepository(BaseRepository):
    """Репозиторий для переводов назначений товаров."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductApplicationTranslation)

    async def add_translation(
        self, data: Union[ProductApplicationTranslationInsert, dict, Any]
    ) -> ProductApplicationTranslation:
        """Добавление перевода."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> Optional[ProductApplicationTranslation]:
        """Получение перевода по ID."""
        stmt = select(ProductApplicationTranslation).where(
            ProductApplicationTranslation.id == translation_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_application_and_locale(
        self, app_id: int, locale: Language
    ) -> Optional[ProductApplicationTranslation]:
        """Получение перевода по ID назначения и локали."""
        stmt = select(ProductApplicationTranslation).where(
            ProductApplicationTranslation.application_id == app_id,
            ProductApplicationTranslation.locale == locale,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода по ID."""
        stmt = (
            update(ProductApplicationTranslation)
            .where(ProductApplicationTranslation.id == translation_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода по ID."""
        stmt = delete(ProductApplicationTranslation).where(
            ProductApplicationTranslation.id == translation_id
        )
        await self.session.execute(stmt)

    async def count_by_application_id(self, app_id: int) -> int:
        """Подсчет количества переводов назначения."""
        stmt = select(func.count(ProductApplicationTranslation.id)).where(
            ProductApplicationTranslation.application_id == app_id
        )
        result = await self.session.scalar(stmt)
        return int(result or 0)


class ProductAssignedApplicationRepository(BaseRepository):
    """Репозиторий для связей товар-назначение (ProductAssignedApplication)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductAssignedApplication)

    async def exists_assignment(self, product_id: int, application_id: int) -> bool:
        """Проверка существования связи товара с назначением."""
        stmt = select(
            exists().where(
                ProductAssignedApplication.product_id == product_id,
                ProductAssignedApplication.application_id == application_id,
            )
        )
        result = await self.session.scalar(stmt)
        return bool(result)

    async def assign_application(
        self, product_id: int, application_id: int
    ) -> ProductAssignedApplication:
        """Создание связи товара с назначением."""
        assignment = ProductAssignedApplication(
            product_id=product_id,
            application_id=application_id,
        )
        self.session.add(assignment)
        return assignment

    async def unassign_application(self, product_id: int, application_id: int) -> None:
        """Удаление связи товара с назначением."""
        stmt = delete(ProductAssignedApplication).where(
            ProductAssignedApplication.product_id == product_id,
            ProductAssignedApplication.application_id == application_id,
        )
        await self.session.execute(stmt)

    async def get_by_product_id(self, product_id: int) -> Sequence[ProductAssignedApplication]:
        """Получение всех назначений, привязанных к товару, с предзагрузкой application и его translations, отсортированных по application.index."""
        stmt = (
            select(ProductAssignedApplication)
            .join(ProductApplication, ProductAssignedApplication.application_id == ProductApplication.id)
            .where(ProductAssignedApplication.product_id == product_id)
            .options(
                selectinload(ProductAssignedApplication.application).selectinload(
                    ProductApplication.translations
                )
            )
            .order_by(ProductApplication.index.asc(), ProductApplication.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
