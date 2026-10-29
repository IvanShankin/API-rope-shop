from src.modules.products.models import Product
from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseRepository
from src.modules.splice_types.models import SpliceType, SpliceTypeTranslation, SpliceCategory
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.rope_allowed_splice.models import RopeAllowedSplice


class SpliceTypeRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=SpliceType)

    async def add_type(self, data: Union[dict, Any]) -> SpliceType:
        """Добавление нового типа услуги."""
        return self.add(data)

    async def get_all(self, is_active: Optional[bool] = None) -> Sequence[SpliceType]:
        """Получение списка всех типов услуг."""
        stmt = select(SpliceType).options(
            selectinload(SpliceType.translations)
        )
        if is_active is not None:
            stmt = stmt.where(SpliceType.is_active == is_active)
        
        stmt = stmt.order_by(SpliceType.index.asc(), SpliceType.id.asc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def get_by_category(self, category: SpliceCategory, is_active: Optional[bool] = None) -> Sequence[SpliceType]:
        """Получение услуг по категории (например, только петли или только сращивания)."""
        stmt = select(SpliceType).options(
            selectinload(SpliceType.translations)
        ).where(SpliceType.category == category)
        
        if is_active is not None:
            stmt = stmt.where(SpliceType.is_active == is_active)
            
        stmt = stmt.order_by(SpliceType.index.asc(), SpliceType.id.asc())
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, type_id: int) -> SpliceType | None:
        """Получение услуги по ID."""
        stmt = select(SpliceType).options(
            selectinload(SpliceType.translations)
        ).where(SpliceType.id == type_id)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> SpliceType | None:
        """Получение услуги по уникальному коду."""
        stmt = select(SpliceType).options(
            selectinload(SpliceType.translations)
        ).where(SpliceType.code == code)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_dependencies(self, type_id: int) -> bool:
        """Проверка наличия связей (правила цен или привязанные веревки)."""
        rules_exist_stmt = select(exists().where(SplicePriceRule.splice_type_id == type_id))
        ropes_exist_stmt = select(exists().where(RopeAllowedSplice.splice_type_id == type_id))

        has_rules = await self.session.scalar(rules_exist_stmt)
        has_ropes = await self.session.scalar(ropes_exist_stmt)

        return bool(has_rules or has_ropes)

    async def get_dependencies(self, type_id: int) -> dict:
        """Получение списка зависимостей (правила цен и привязанные канаты)."""
        rules_stmt = (
            select(SplicePriceRule)
            .where(SplicePriceRule.splice_type_id == type_id)
            .order_by(SplicePriceRule.id)
        )
        rules = (await self.session.execute(rules_stmt)).scalars().all()

        ropes_stmt = (
            select(Product)
            .join(RopeAllowedSplice, RopeAllowedSplice.product_id == Product.id)
            .options(selectinload(Product.translations))
            .where(RopeAllowedSplice.splice_type_id == type_id)
            .order_by(Product.id)
        )
        ropes = (await self.session.execute(ropes_stmt)).scalars().all()

        return {
            "rules": rules,
            "ropes": ropes,
        }

    async def update_type(self, type_id: int, update_data: dict) -> None:
        """Обновление данных услуги."""
        stmt = update(SpliceType).where(SpliceType.id == type_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_type(self, type_id: int) -> None:
        """Удаление услуги."""
        stmt = delete(SpliceType).where(SpliceType.id == type_id)
        await self.session.execute(stmt)


class SpliceTypeTranslationRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=SpliceTypeTranslation)

    async def add_translation(self, data: Union[dict, Any]) -> SpliceTypeTranslation:
        """Добавление перевода для услуги."""
        return self.add(data)

    async def get_by_id(self, translation_id: int) -> SpliceTypeTranslation | None:
        """Получение перевода по ID."""
        stmt = select(SpliceTypeTranslation).where(SpliceTypeTranslation.id == translation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_type_and_locale(self, type_id: int, locale: Language) -> SpliceTypeTranslation | None:
        """Получение перевода для конкретной услуги и языка."""
        stmt = select(SpliceTypeTranslation).where(
            SpliceTypeTranslation.splice_type_id == type_id,
            SpliceTypeTranslation.locale == locale
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_translation(self, translation_id: int, update_data: dict) -> None:
        """Обновление перевода."""
        stmt = update(SpliceTypeTranslation).where(SpliceTypeTranslation.id == translation_id).values(**update_data)
        await self.session.execute(stmt)

    async def delete_translation(self, translation_id: int) -> None:
        """Удаление перевода."""
        stmt = delete(SpliceTypeTranslation).where(SpliceTypeTranslation.id == translation_id)
        await self.session.execute(stmt)
