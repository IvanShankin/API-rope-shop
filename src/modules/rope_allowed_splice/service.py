from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import Language
from src.modules.products.models import Product
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
        """Привязка типа сращивания к товару."""
        if not await self.repo.exists_product(data.product_id):
            raise RopeProductNotFound(
                f"Product with id {data.product_id} not found."
            )

        if not await self.repo.exists_splice_type(data.splice_type_id):
            raise SpliceTypeNotFound(
                f"SpliceType with id {data.splice_type_id} not found."
            )

        existing = await self.repo.get_by_composite_key(
            product_id=data.product_id,
            splice_type_id=data.splice_type_id,
        )
        if existing:
            raise RopeAllowedSpliceAlreadyExists(
                f"SpliceType with id {data.splice_type_id} is already linked to Product with id {data.product_id}."
            )

        await self.repo.add_item(data)
        await self.session.commit()

        loaded_item = await self.repo.get_by_composite_key(
            product_id=data.product_id,
            splice_type_id=data.splice_type_id,
        )
        return RopeAllowedSpliceResponseDTO.model_validate(loaded_item)

    async def set_allowed_splices_for_product(
        self,
        product_id: int,
        data: RopeAllowedSpliceBulkSetDTO
    ) -> List[RopeAllowedSpliceResponseDTO]:
        """Пакетная установка (перезапись) разрешенных типов сращиваний для товара."""
        if not await self.repo.exists_product(product_id):
            raise RopeProductNotFound(
                f"Product with id {product_id} not found."
            )

        unique_splice_ids = list(dict.fromkeys(data.splice_type_ids))

        for splice_id in unique_splice_ids:
            if not await self.repo.exists_splice_type(splice_id):
                raise SpliceTypeNotFound(
                    f"SpliceType with id {splice_id} not found."
                )

        await self.repo.delete_by_product_id(product_id)

        for splice_id in unique_splice_ids:
            item_dto = RopeAllowedSpliceBase(
                product_id=product_id,
                splice_type_id=splice_id
            )
            await self.repo.add_item(item_dto)

        await self.session.commit()

        items = await self.repo.get_by_product_id(product_id)
        return [RopeAllowedSpliceResponseDTO.model_validate(item) for item in items]

    async def get_allowed_splices_by_product_id(
        self,
        product_id: int,
        locale: Optional[Language] = None,
        is_admin: bool = False,
    ) -> List[RopeAllowedSpliceLocalizedResponseDTO]:
        """Получение списка разрешенных типов сращиваний для товара с локализацией."""
        product = await self.session.get(Product, product_id)
        if not product or (not is_admin and not product.is_active):
            raise RopeProductNotFound(
                f"Product with id {product_id} not found."
            )

        items = await self.repo.get_by_product_id(product_id)
        target_locale = locale or Language.ENG

        result: List[RopeAllowedSpliceLocalizedResponseDTO] = []
        for item in items:
            if not is_admin and item.splice_type and not item.splice_type.is_active:
                continue
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
                    product_id=item.product_id,
                    splice_type_id=item.splice_type_id,
                    splice_type=localized_splice
                )
            )

        return result

    async def get_by_composite_key(
        self,
        product_id: int,
        splice_type_id: int,
        is_admin: bool = False,
    ) -> RopeAllowedSpliceResponseDTO:
        """Получение привязки по составному ключу."""
        item = await self.repo.get_by_composite_key(
            product_id=product_id,
            splice_type_id=splice_type_id
        )
        if not item or (not is_admin and ((item.splice_type and not item.splice_type.is_active) or (item.product and not item.product.is_active))):
            raise RopeAllowedSpliceNotFound(
                f"RopeAllowedSplice with product_id {product_id} and splice_type_id {splice_type_id} not found."
            )
        return RopeAllowedSpliceResponseDTO.model_validate(item)

    async def delete_rope_allowed_splice(
        self,
        product_id: int,
        splice_type_id: int
    ) -> None:
        """Удаление привязки типа сращивания к товару."""
        item = await self.repo.get_by_composite_key(
            product_id=product_id,
            splice_type_id=splice_type_id
        )
        if not item:
            raise RopeAllowedSpliceNotFound(
                f"RopeAllowedSplice with product_id {product_id} and splice_type_id {splice_type_id} not found."
            )

        await self.repo.delete_item(
            product_id=product_id,
            splice_type_id=splice_type_id
        )
        await self.session.commit()
