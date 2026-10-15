from typing import Sequence

from sqlalchemy import select, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseIndexedRepository
from src.modules.colors.models import Color
from src.modules.products.models import Product
from src.modules.rope_product_color.models import ProductColor
from src.modules.rope_product_color.models_dto import ProductColorBase


class ProductColorRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductColor)

    async def add_item(self, data: ProductColorBase) -> ProductColor:
        """Добавление новой привязки цвета к товару."""
        return self.add(data.model_dump())

    async def get_by_id(self, item_id: int) -> ProductColor | None:
        """Получение привязки по ID с предзагрузкой цвета и его переводов."""
        stmt = (
            select(ProductColor)
            .options(
                selectinload(ProductColor.color)
                .selectinload(Color.translations)
            )
            .where(ProductColor.id == item_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(self, product_id: int) -> Sequence[ProductColor]:
        """Получение всех цветов товара в порядке возрастания index."""
        stmt = (
            select(ProductColor)
            .options(
                selectinload(ProductColor.color)
                .selectinload(Color.translations)
            )
            .where(ProductColor.product_id == product_id)
            .order_by(ProductColor.index)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_product_and_color(
        self,
        product_id: int,
        color_id: int
    ) -> ProductColor | None:
        """Поиск привязки по паре (product_id, color_id)."""
        stmt = select(ProductColor).where(
            ProductColor.product_id == product_id,
            ProductColor.color_id == color_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_product(self, product_id: int) -> bool:
        """Проверка существования товара."""
        stmt = select(exists().where(Product.id == product_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_color(self, color_id: int) -> bool:
        """Проверка существования цвета."""
        stmt = select(exists().where(Color.id == color_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def delete_item(self, item_id: int) -> None:
        """Удаление привязки цвета по ID."""
        stmt = delete(ProductColor).where(ProductColor.id == item_id)
        await self.session.execute(stmt)
