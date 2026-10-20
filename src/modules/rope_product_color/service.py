from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.products.models import Product
from src.modules.colors.models_dto import ColorLocalizedResponseDTO
from src.modules.rope_product_color.repository import ProductColorRepository
from src.modules.rope_product_color.models_dto import (
    ProductColorBase,
    ProductColorCreate,
    ProductColorUpdateIndexDTO,
    ProductColorResponseDTO,
    ProductColorLocalizedResponseDTO,
)
from src.modules.rope_product_color.exception import (
    RopeProductColorNotFound,
    RopeProductColorAlreadyExists,
    RopeProductNotFound,
    ColorNotFound,
)


class RopeProductColorService:
    def __init__(
        self,
        repo: ProductColorRepository,
        session: AsyncSession,
    ):
        self.repo = repo
        self.session = session

    async def create_rope_product_color(
        self,
        data: ProductColorCreate
    ) -> ProductColorResponseDTO:
        """Привязка цвета к товару с добавлением в конец списка (максимальный индекс + 1)."""
        if not await self.repo.exists_product(data.product_id):
            raise RopeProductNotFound(
                f"Product with id {data.product_id} not found."
            )

        if not await self.repo.exists_color(data.color_id):
            raise ColorNotFound(
                f"Color with id {data.color_id} not found."
            )

        existing = await self.repo.get_by_product_and_color(
            product_id=data.product_id,
            color_id=data.color_id
        )
        if existing:
            raise RopeProductColorAlreadyExists(
                f"Color with id {data.color_id} is already linked to Product with id {data.product_id}."
            )

        max_index = await self.repo.get_max_index(
            product_id=data.product_id
        )
        target_index = max_index + 1

        item_dto = ProductColorBase(
            product_id=data.product_id,
            color_id=data.color_id,
            index=target_index
        )
        new_item = await self.repo.add_item(item_dto)
        await self.session.commit()

        loaded_item = await self.repo.get_by_id(new_item.id)
        return ProductColorResponseDTO.model_validate(loaded_item)

    async def get_colors_by_product_id(
        self,
        product_id: int,
        locale: Optional[Language] = None,
        is_admin: bool = False,
    ) -> List[ProductColorLocalizedResponseDTO]:
        """Получение списка цветов для товара с локализацией названий цветов."""
        product = await self.session.get(Product, product_id)
        if not product or (not is_admin and not product.is_active):
            raise RopeProductNotFound(
                f"Product with id {product_id} not found."
            )

        items = await self.repo.get_by_product_id(product_id)
        target_locale = locale or Language.ENG

        result: List[ProductColorLocalizedResponseDTO] = []
        for item in items:
            if not is_admin and item.color and not item.color.is_active:
                continue
            localized_color: Optional[ColorLocalizedResponseDTO] = None
            if item.color:
                name = item.color._get_field_with_translation(
                    lambda t: t.name,
                    target_locale
                )
                localized_color = ColorLocalizedResponseDTO(
                    id=item.color.id,
                    code=item.color.code,
                    hex=item.color.hex,
                    index=item.color.index,
                    is_active=item.color.is_active,
                    name=name if name else "No Translation",
                )

            result.append(
                ProductColorLocalizedResponseDTO(
                    id=item.id,
                    product_id=item.product_id,
                    color_id=item.color_id,
                    index=item.index,
                    color=localized_color
                )
            )

        return result

    async def get_by_id(self, item_id: int, is_admin: bool = False) -> ProductColorResponseDTO:
        """Получение привязки цвета по ID."""
        item = await self.repo.get_by_id(item_id)
        if not item or (not is_admin and ((item.color and not item.color.is_active) or (item.product and not item.product.is_active))):
            raise RopeProductColorNotFound(
                f"ProductColor with id {item_id} not found."
            )
        return ProductColorResponseDTO.model_validate(item)

    async def reorder_color(
        self,
        item_id: int,
        data: ProductColorUpdateIndexDTO
    ) -> ProductColorResponseDTO:
        """Изменение позиции цвета внутри конкретного товара со сдвигом соседей."""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise RopeProductColorNotFound(
                f"ProductColor with id {item_id} not found."
            )

        if item.index != data.new_index:
            await self.repo.reorder_index(
                obj_id=item_id,
                old_index=item.index,
                new_index=data.new_index,
                product_id=item.product_id
            )
            await self.session.commit()

        updated_item = await self.repo.get_by_id(item_id)
        return ProductColorResponseDTO.model_validate(updated_item)

    async def delete_rope_product_color(self, item_id: int) -> None:
        """Удаление привязки цвета и сдвиг оставшихся индексов для устранения пробелов."""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise RopeProductColorNotFound(
                f"ProductColor with id {item_id} not found."
            )

        deleted_index = item.index
        product_id = item.product_id

        await self.repo.delete_item(item_id)
        await self.repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            product_id=product_id
        )
        await self.session.commit()
