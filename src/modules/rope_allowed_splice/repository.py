from typing import Sequence

from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository
from src.modules.products.models import Product
from src.modules.splice_types.models import SpliceType
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceBase


class RopeAllowedSpliceRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=RopeAllowedSplice)

    async def add_item(self, data: RopeAllowedSpliceBase) -> RopeAllowedSplice:
        """Добавление новой привязки разрешенного сращивания к товару."""
        return self.add(data.model_dump())

    async def get_by_composite_key(
        self,
        product_id: int,
        splice_type_id: int
    ) -> RopeAllowedSplice | None:
        """Получение записи по составному ключу (product_id, splice_type_id)."""
        stmt = (
            select(RopeAllowedSplice)
            .options(
                selectinload(RopeAllowedSplice.splice_type)
                .selectinload(SpliceType.translations)
            )
            .where(
                RopeAllowedSplice.product_id == product_id,
                RopeAllowedSplice.splice_type_id == splice_type_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(
        self,
        product_id: int
    ) -> Sequence[RopeAllowedSplice]:
        """Получение всех разрешенных сращиваний товара с предзагрузкой сплайс-типов и переводов."""
        stmt = (
            select(RopeAllowedSplice)
            .join(RopeAllowedSplice.splice_type)
            .options(
                selectinload(RopeAllowedSplice.splice_type)
                .selectinload(SpliceType.translations)
            )
            .where(RopeAllowedSplice.product_id == product_id)
            .order_by(SpliceType.index.asc(), SpliceType.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def exists_product(self, product_id: int) -> bool:
        """Проверка существования товара."""
        stmt = select(exists().where(Product.id == product_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_splice_type(self, splice_type_id: int) -> bool:
        """Проверка существования типа сращивания."""
        stmt = select(exists().where(SpliceType.id == splice_type_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def delete_item(
        self,
        product_id: int,
        splice_type_id: int
    ) -> None:
        """Удаление записи по составному ключу."""
        stmt = delete(RopeAllowedSplice).where(
            RopeAllowedSplice.product_id == product_id,
            RopeAllowedSplice.splice_type_id == splice_type_id,
        )
        await self.session.execute(stmt)

    async def delete_by_product_id(self, product_id: int) -> None:
        """Удаление всех разрешенных сращиваний для товара."""
        stmt = delete(RopeAllowedSplice).where(
            RopeAllowedSplice.product_id == product_id
        )
        await self.session.execute(stmt)
