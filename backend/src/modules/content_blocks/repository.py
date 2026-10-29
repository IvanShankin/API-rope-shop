from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.database_model import Language
from src.modules.base.repository_model import BaseRepository
from src.modules.content_blocks.models import ContentBlock, ContentBlockTranslation


class ContentBlockRepository(BaseRepository[ContentBlock]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ContentBlock)

    async def get_by_id(self, block_id: int) -> Optional[ContentBlock]:
        """Получение блока по ID с жадной загрузкой всех переводов."""
        stmt = (
            select(ContentBlock)
            .where(ContentBlock.id == block_id)
            .options(selectinload(ContentBlock.translations))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_block_code(
        self,
        block_code: str,
        page_code: Optional[str] = None,
    ) -> Optional[ContentBlock]:
        """Получение блока по block_code (и опционально page_code) с жадной загрузкой переводов."""
        stmt = (
            select(ContentBlock)
            .where(ContentBlock.block_code == block_code)
            .options(selectinload(ContentBlock.translations))
        )
        if page_code:
            stmt = stmt.where(ContentBlock.page_code == page_code)
        stmt = stmt.order_by(ContentBlock.index.asc(), ContentBlock.id.asc()).limit(1)
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_by_page_and_block_code(
        self,
        page_code: str,
        block_code: str,
    ) -> Optional[ContentBlock]:
        """Получение блока по составному ключу (page_code, block_code) с жадной загрузкой переводов."""
        stmt = (
            select(ContentBlock)
            .where(
                ContentBlock.page_code == page_code,
                ContentBlock.block_code == block_code,
            )
            .options(selectinload(ContentBlock.translations))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_page_code(
        self,
        page_code: str,
        is_active: Optional[bool] = None,
    ) -> List[ContentBlock]:
        """
        Получение всех блоков для указанного page_code с загруженными переводами.
        Опциональная фильтрация по is_active, стабильная сортировка по index, id.
        """
        stmt = (
            select(ContentBlock)
            .where(ContentBlock.page_code == page_code)
            .options(selectinload(ContentBlock.translations))
            .order_by(ContentBlock.index.asc(), ContentBlock.id.asc())
        )
        if is_active is not None:
            stmt = stmt.where(ContentBlock.is_active == is_active)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    def add_block(self, obj: ContentBlock) -> ContentBlock:
        """Добавление сущности ContentBlock в сессию."""
        self.session.add(obj)
        return obj

    async def update_block(self, block_id: int, values: dict) -> None:
        """Обновление полей блока контента."""
        if not values:
            return
        stmt = (
            update(ContentBlock)
            .where(ContentBlock.id == block_id)
            .values(**values)
        )
        await self.session.execute(stmt)


class ContentBlockTranslationRepository(BaseRepository[ContentBlockTranslation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ContentBlockTranslation)

    async def get_by_block_and_locale(
        self,
        block_id: int,
        locale: Language,
    ) -> Optional[ContentBlockTranslation]:
        """Поиск перевода для блока по языковой локали."""
        stmt = select(ContentBlockTranslation).where(
            ContentBlockTranslation.content_block_id == block_id,
            ContentBlockTranslation.locale == locale,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_translations_by_block_id(
        self,
        block_id: int,
    ) -> List[ContentBlockTranslation]:
        """Получение всех переводов блока контента."""
        stmt = (
            select(ContentBlockTranslation)
            .where(ContentBlockTranslation.content_block_id == block_id)
            .order_by(ContentBlockTranslation.id)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    def add_translation(
        self,
        obj: ContentBlockTranslation,
    ) -> ContentBlockTranslation:
        """Добавление перевода в сессию."""
        self.session.add(obj)
        return obj

    async def update_translation(self, trans_id: int, values: dict) -> None:
        """Обновление полей перевода."""
        if not values:
            return
        stmt = (
            update(ContentBlockTranslation)
            .where(ContentBlockTranslation.id == trans_id)
            .values(**values)
        )
        await self.session.execute(stmt)
