from typing import Any, Optional, Sequence, Union

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseIndexedRepository
from src.modules.product_images.models import ProductImage
from src.modules.product_images.models_dto import ProductImageBase


class ProductImageRepository(BaseIndexedRepository):
    """Репозиторий для работы с изображениями товаров (ProductImage)."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductImage)

    def add_image(
        self, data: Union[ProductImageBase, dict, Any]
    ) -> ProductImage:
        """Добавление новой записи изображения товара."""
        return self.add(data)

    async def get_by_id(self, image_id: int) -> Optional[ProductImage]:
        """Получение изображения по ID."""
        stmt = select(ProductImage).where(ProductImage.id == image_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(
        self,
        product_id: int,
        is_active: Optional[bool] = None,
    ) -> Sequence[ProductImage]:
        """Получение списка изображений товара, отсортированных по index."""
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.index)
        )
        if is_active is not None:
            stmt = stmt.where(ProductImage.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_main_image(self, product_id: int) -> Optional[ProductImage]:
        """Получение главного изображения товара."""
        stmt = select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.is_main.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_product_id(
        self,
        product_id: int,
        is_active: Optional[bool] = None,
    ) -> int:
        """Подсчет количества изображений товара."""
        stmt = select(func.count(ProductImage.id)).where(ProductImage.product_id == product_id)
        if is_active is not None:
            stmt = stmt.where(ProductImage.is_active == is_active)
        result = await self.session.scalar(stmt)
        return int(result or 0)

    async def reset_main_images(
        self,
        product_id: int,
        exclude_image_id: Optional[int] = None,
    ) -> None:
        """Сброс флага is_main для всех изображений товара, кроме exclude_image_id."""
        stmt = (
            update(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.is_main.is_(True),
            )
            .values(is_main=False)
        )
        if exclude_image_id is not None:
            stmt = stmt.where(ProductImage.id != exclude_image_id)
        await self.session.execute(stmt)

    async def update_image(self, image_id: int, update_data: dict) -> None:
        """Обновление атрибутов изображения по ID."""
        stmt = (
            update(ProductImage)
            .where(ProductImage.id == image_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_image(self, image_id: int) -> None:
        """Удаление записи изображения по ID."""
        stmt = delete(ProductImage).where(ProductImage.id == image_id)
        await self.session.execute(stmt)

    async def has_dependencies(self, image_id: int) -> bool:
        """Проверка зависимостей изображения (изображение не имеет дочерних связей)."""
        return False
