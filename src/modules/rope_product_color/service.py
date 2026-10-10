from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.colors.models_dto import ColorLocalizedResponseDTO
from src.modules.rope_product_color.repository import RopeProductColorRepository
from src.modules.rope_product_color.models_dto import (
    RopeProductColorBase,
    RopeProductColorCreate,
    RopeProductColorUpdateIndexDTO,
    RopeProductColorResponseDTO,
    RopeProductColorLocalizedResponseDTO,
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
        repo: RopeProductColorRepository,
        session: AsyncSession,
    ):
        self.repo = repo
        self.session = session

    async def create_rope_product_color(
        self,
        data: RopeProductColorCreate
    ) -> RopeProductColorResponseDTO:
        """Привязка цвета к товару-веревке с добавлением в конец списка (максимальный индекс + 1)."""
        if not await self.repo.exists_product(data.rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with id {data.rope_product_id} not found."
            )

        if not await self.repo.exists_color(data.color_id):
            raise ColorNotFound(
                f"Color with id {data.color_id} not found."
            )

        existing = await self.repo.get_by_product_and_color(
            rope_product_id=data.rope_product_id,
            color_id=data.color_id
        )
        if existing:
            raise RopeProductColorAlreadyExists(
                f"Color with id {data.color_id} is already linked to RopeProduct with id {data.rope_product_id}."
            )

        max_index = await self.repo.get_max_index(
            rope_product_id=data.rope_product_id
        )
        target_index = max_index + 1

        item_dto = RopeProductColorBase(
            rope_product_id=data.rope_product_id,
            color_id=data.color_id,
            index=target_index
        )
        new_item = await self.repo.add_item(item_dto)
        await self.session.commit()

        loaded_item = await self.repo.get_by_id(new_item.id)
        return RopeProductColorResponseDTO.model_validate(loaded_item)

    async def get_colors_by_product_id(
        self,
        rope_product_id: int,
        locale: Optional[Language] = None
    ) -> List[RopeProductColorLocalizedResponseDTO]:
        """Получение списка цветов для товара с локализацией названий цветов."""
        if not await self.repo.exists_product(rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with id {rope_product_id} not found."
            )

        items = await self.repo.get_by_product_id(rope_product_id)
        target_locale = locale or Language.ENG

        result: List[RopeProductColorLocalizedResponseDTO] = []
        for item in items:
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
                RopeProductColorLocalizedResponseDTO(
                    id=item.id,
                    rope_product_id=item.rope_product_id,
                    color_id=item.color_id,
                    index=item.index,
                    color=localized_color
                )
            )

        return result

    async def get_by_id(self, item_id: int) -> RopeProductColorResponseDTO:
        """Получение привязки цвета по ID."""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise RopeProductColorNotFound(
                f"RopeProductColor with id {item_id} not found."
            )
        return RopeProductColorResponseDTO.model_validate(item)

    async def reorder_color(
        self,
        item_id: int,
        data: RopeProductColorUpdateIndexDTO
    ) -> RopeProductColorResponseDTO:
        """Изменение позиции цвета внутри конкретного товара со сдвигом соседей."""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise RopeProductColorNotFound(
                f"RopeProductColor with id {item_id} not found."
            )

        if item.index != data.new_index:
            await self.repo.reorder_index(
                obj_id=item_id,
                old_index=item.index,
                new_index=data.new_index,
                rope_product_id=item.rope_product_id
            )
            await self.session.commit()

        updated_item = await self.repo.get_by_id(item_id)
        return RopeProductColorResponseDTO.model_validate(updated_item)

    async def delete_rope_product_color(self, item_id: int) -> None:
        """Удаление привязки цвета и сдвиг оставшихся индексов для устранения пробелов."""
        item = await self.repo.get_by_id(item_id)
        if not item:
            raise RopeProductColorNotFound(
                f"RopeProductColor with id {item_id} not found."
            )

        deleted_index = item.index
        product_id = item.rope_product_id

        await self.repo.delete_item(item_id)
        await self.repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            rope_product_id=product_id
        )
        await self.session.commit()
