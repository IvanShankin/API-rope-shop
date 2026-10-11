from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.splice_types.models_dto import SpliceTypeLocalizedResponseDTO
from src.modules.rope_allowed_splice.repository import RopeAllowedSpliceRepository
from src.modules.rope_allowed_splice.models_dto import (
    RopeAllowedSpliceBase,
    RopeAllowedSpliceCreate,
    RopeAllowedSpliceBulkSetDTO,
    RopeAllowedSpliceResponseDTO,
    RopeAllowedSpliceLocalizedResponseDTO,
)
from src.modules.rope_allowed_splice.exception import (
    RopeAllowedSpliceNotFound,
    RopeAllowedSpliceAlreadyExists,
    RopeProductNotFound,
    SpliceTypeNotFound,
)


class RopeAllowedSpliceService:
    def __init__(
        self,
        repo: RopeAllowedSpliceRepository,
        session: AsyncSession,
    ):
        self.repo = repo
        self.session = session

    async def create_rope_allowed_splice(
        self,
        data: RopeAllowedSpliceCreate
    ) -> RopeAllowedSpliceResponseDTO:
        """Привязка типа сращивания к товару-веревке."""
        if not await self.repo.exists_product(data.rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with id {data.rope_product_id} not found."
            )

        if not await self.repo.exists_splice_type(data.splice_type_id):
            raise SpliceTypeNotFound(
                f"SpliceType with id {data.splice_type_id} not found."
            )

        existing = await self.repo.get_by_composite_key(
            rope_product_id=data.rope_product_id,
            splice_type_id=data.splice_type_id,
        )
        if existing:
            raise RopeAllowedSpliceAlreadyExists(
                f"SpliceType with id {data.splice_type_id} is already linked to RopeProduct with id {data.rope_product_id}."
            )

        await self.repo.add_item(data)
        await self.session.commit()

        loaded_item = await self.repo.get_by_composite_key(
            rope_product_id=data.rope_product_id,
            splice_type_id=data.splice_type_id,
        )
        return RopeAllowedSpliceResponseDTO.model_validate(loaded_item)

    async def set_allowed_splices_for_product(
        self,
        rope_product_id: int,
        data: RopeAllowedSpliceBulkSetDTO
    ) -> List[RopeAllowedSpliceResponseDTO]:
        """Пакетная установка (перезапись) разрешенных типов сращиваний для товара-веревки."""
        if not await self.repo.exists_product(rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with id {rope_product_id} not found."
            )

        unique_splice_ids = list(dict.fromkeys(data.splice_type_ids))

        for splice_id in unique_splice_ids:
            if not await self.repo.exists_splice_type(splice_id):
                raise SpliceTypeNotFound(
                    f"SpliceType with id {splice_id} not found."
                )

        await self.repo.delete_by_product_id(rope_product_id)

        for splice_id in unique_splice_ids:
            item_dto = RopeAllowedSpliceBase(
                rope_product_id=rope_product_id,
                splice_type_id=splice_id
            )
            await self.repo.add_item(item_dto)

        await self.session.commit()

        items = await self.repo.get_by_product_id(rope_product_id)
        return [RopeAllowedSpliceResponseDTO.model_validate(item) for item in items]

    async def get_allowed_splices_by_product_id(
        self,
        rope_product_id: int,
        locale: Optional[Language] = None
    ) -> List[RopeAllowedSpliceLocalizedResponseDTO]:
        """Получение списка разрешенных типов сращиваний для товара с локализацией."""
        if not await self.repo.exists_product(rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with id {rope_product_id} not found."
            )

        items = await self.repo.get_by_product_id(rope_product_id)
        target_locale = locale or Language.ENG

        result: List[RopeAllowedSpliceLocalizedResponseDTO] = []
        for item in items:
            localized_splice: Optional[SpliceTypeLocalizedResponseDTO] = None
            if item.splice_type:
                name = item.splice_type._get_field_with_translation(
                    lambda t: t.name,
                    target_locale
                )
                description = item.splice_type._get_field_with_translation(
                    lambda t: t.description,
                    target_locale
                )
                localized_splice = SpliceTypeLocalizedResponseDTO(
                    id=item.splice_type.id,
                    code=item.splice_type.code,
                    category=item.splice_type.category,
                    visual_type=item.splice_type.visual_type,
                    image_url=item.splice_type.image_url,
                    index=item.splice_type.index,
                    is_active=item.splice_type.is_active,
                    created_at=item.splice_type.created_at,
                    updated_at=item.splice_type.updated_at,
                    name=name if name else "No Translation",
                    description=description,
                )

            result.append(
                RopeAllowedSpliceLocalizedResponseDTO(
                    rope_product_id=item.rope_product_id,
                    splice_type_id=item.splice_type_id,
                    splice_type=localized_splice
                )
            )

        return result

    async def get_by_composite_key(
        self,
        rope_product_id: int,
        splice_type_id: int
    ) -> RopeAllowedSpliceResponseDTO:
        """Получение привязки по составному ключу."""
        item = await self.repo.get_by_composite_key(
            rope_product_id=rope_product_id,
            splice_type_id=splice_type_id
        )
        if not item:
            raise RopeAllowedSpliceNotFound(
                f"RopeAllowedSplice with rope_product_id {rope_product_id} and splice_type_id {splice_type_id} not found."
            )
        return RopeAllowedSpliceResponseDTO.model_validate(item)

    async def delete_rope_allowed_splice(
        self,
        rope_product_id: int,
        splice_type_id: int
    ) -> None:
        """Удаление привязки типа сращивания к товару."""
        item = await self.repo.get_by_composite_key(
            rope_product_id=rope_product_id,
            splice_type_id=splice_type_id
        )
        if not item:
            raise RopeAllowedSpliceNotFound(
                f"RopeAllowedSplice with rope_product_id {rope_product_id} and splice_type_id {splice_type_id} not found."
            )

        await self.repo.delete_item(
            rope_product_id=rope_product_id,
            splice_type_id=splice_type_id
        )
        await self.session.commit()
