from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseIndexedRepository
from src.modules.colors.models import Color
from src.modules.rope_products.models import RopeProduct
from src.modules.rope_product_color.models import RopeProductColor


class RopeProductColorRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=RopeProductColor)

    async def add_item(self, data: Union[dict, Any]) -> RopeProductColor:
        """Добавление новой привязки цвета к товару."""
        return self.add(data)

    async def get_by_id(self, item_id: int) -> RopeProductColor | None:
        """Получение привязки по ID с предзагрузкой цвета и его переводов."""
        stmt = (
            select(RopeProductColor)
            .options(
                selectinload(RopeProductColor.color)
                .selectinload(Color.translations)
            )
            .where(RopeProductColor.id == item_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(self, rope_product_id: int) -> Sequence[RopeProductColor]:
        """Получение всех цветов товара в порядке возрастания index."""
        stmt = (
            select(RopeProductColor)
            .options(
                selectinload(RopeProductColor.color)
                .selectinload(Color.translations)
            )
            .where(RopeProductColor.rope_product_id == rope_product_id)
            .order_by(RopeProductColor.index)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_product_and_color(
        self,
        rope_product_id: int,
        color_id: int
    ) -> RopeProductColor | None:
        """Поиск привязки по паре (rope_product_id, color_id)."""
        stmt = select(RopeProductColor).where(
            RopeProductColor.rope_product_id == rope_product_id,
            RopeProductColor.color_id == color_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_product(self, rope_product_id: int) -> bool:
        """Проверка существования товара-веревки."""
        stmt = select(exists().where(RopeProduct.product_id == rope_product_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_color(self, color_id: int) -> bool:
        """Проверка существования цвета."""
        stmt = select(exists().where(Color.id == color_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def delete_item(self, item_id: int) -> None:
        """Удаление привязки цвета по ID."""
        stmt = delete(RopeProductColor).where(RopeProductColor.id == item_id)
        await self.session.execute(stmt)
