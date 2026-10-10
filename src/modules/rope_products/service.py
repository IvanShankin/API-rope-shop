from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NoDataForUpdate
from src.modules.products.models import Product
from src.modules.rope_products.repository import RopeProductRepository, RopeVariantRepository
from src.modules.rope_products.models_dto import (
    RopeProductCreate,
    RopeProductUpdate,
    RopeProductResponseDTO,
    RopeProductDetailResponseDTO,
    RopeVariantBase,
    RopeVariantCreate,
    RopeVariantUpdate,
    RopeVariantUpdateIndexDTO,
    RopeVariantResponseDTO,
)
from src.modules.rope_products.exception import (
    RopeProductNotFound,
    RopeProductAlreadyExists,
    RopeVariantNotFound,
    RopeVariantAlreadyExists,
    MaterialGroupNotFound,
    SpliceMaterialNotFound,
)


class RopeProductsService:
    def __init__(
        self,
        product_repo: RopeProductRepository,
        variant_repo: RopeVariantRepository,
        session: AsyncSession,
    ):
        self.product_repo = product_repo
        self.variant_repo = variant_repo
        self.session = session

    # ==================== RopeProduct Operations ====================

    async def create_rope_product(
        self,
        data: RopeProductCreate
    ) -> RopeProductResponseDTO:
        """Создание товара-веревки."""
        if not await self.product_repo.exists_material_group(data.material_group_id):
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {data.material_group_id} not found."
            )

        if not await self.product_repo.exists_splice_material(data.splice_material_id):
            raise SpliceMaterialNotFound(
                f"SpliceMaterial with id {data.splice_material_id} not found."
            )

        if data.product_id is not None:
            if await self.product_repo.exists(data.product_id):
                raise RopeProductAlreadyExists(
                    f"RopeProduct with product_id {data.product_id} already exists."
                )
            if not await self.product_repo.exists_base_product(data.product_id):
                base_product = Product(id=data.product_id)
                self.session.add(base_product)
                await self.session.flush()
            target_product_id = data.product_id
        else:
            base_product = await self.product_repo.create_base_product()
            target_product_id = base_product.id

        product_dict = data.model_dump(exclude={"product_id"})
        product_dict["product_id"] = target_product_id

        new_rope_product = await self.product_repo.add_product(product_dict)
        await self.session.commit()

        loaded = await self.product_repo.get_by_id(new_rope_product.product_id)
        return RopeProductResponseDTO.model_validate(loaded)

    async def get_rope_product(
        self,
        product_id: int
    ) -> RopeProductDetailResponseDTO:
        """Получение детальной информации о товаре-веревке (с вариантами, цветами, сплайсами)."""
        item = await self.product_repo.get_by_id(product_id, include_relations=True)
        if not item:
            raise RopeProductNotFound(
                f"RopeProduct with product_id {product_id} not found."
            )
        return RopeProductDetailResponseDTO.model_validate(item)

    async def list_rope_products(
        self,
        material_group_id: Optional[int] = None,
        can_be_spliced: Optional[bool] = None,
    ) -> List[RopeProductResponseDTO]:
        """Получение списка товаров-веревок с фильтрацией."""
        items = await self.product_repo.get_all(
            material_group_id=material_group_id,
            can_be_spliced=can_be_spliced,
        )
        return [RopeProductResponseDTO.model_validate(i) for i in items]

    async def update_rope_product(
        self,
        product_id: int,
        data: RopeProductUpdate
    ) -> RopeProductResponseDTO:
        """Обновление характеристик товара-веревки."""
        if not await self.product_repo.exists(product_id):
            raise RopeProductNotFound(
                f"RopeProduct with product_id {product_id} not found."
            )

        if data.material_group_id is not None:
            if not await self.product_repo.exists_material_group(data.material_group_id):
                raise MaterialGroupNotFound(
                    f"MaterialGroup with id {data.material_group_id} not found."
                )

        if data.splice_material_id is not None:
            if not await self.product_repo.exists_splice_material(data.splice_material_id):
                raise SpliceMaterialNotFound(
                    f"SpliceMaterial with id {data.splice_material_id} not found."
                )

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("Did not transmit data")

        await self.product_repo.update_product(product_id, update_dict)
        await self.session.commit()

        updated = await self.product_repo.get_by_id(product_id)
        return RopeProductResponseDTO.model_validate(updated)

    async def delete_rope_product(self, product_id: int) -> None:
        """Удаление товара-веревки."""
        if not await self.product_repo.exists(product_id):
            raise RopeProductNotFound(
                f"RopeProduct with product_id {product_id} not found."
            )

        await self.product_repo.delete_product(product_id)
        await self.session.commit()

    # ==================== RopeVariant Operations ====================

    async def create_variant(
        self,
        data: RopeVariantCreate
    ) -> RopeVariantResponseDTO:
        """Добавление варианта/диаметра товара в конец списка (max_index + 1)."""
        if not await self.product_repo.exists(data.rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with product_id {data.rope_product_id} not found."
            )

        existing = await self.variant_repo.get_by_product_and_diameter(
            rope_product_id=data.rope_product_id,
            diameter_mm=data.diameter_mm,
        )
        if existing:
            raise RopeVariantAlreadyExists(
                f"Variant with diameter {data.diameter_mm} mm already exists for RopeProduct {data.rope_product_id}."
            )

        max_index = await self.variant_repo.get_max_index(
            rope_product_id=data.rope_product_id
        )
        target_index = max_index + 1

        variant_dto = RopeVariantBase(
            rope_product_id=data.rope_product_id,
            diameter_mm=data.diameter_mm,
            breaking_load_dan=data.breaking_load_dan,
            weight_g_per_m=data.weight_g_per_m,
            price_per_meter=data.price_per_meter,
            index=target_index,
            is_active=data.is_active,
        )

        new_variant = await self.variant_repo.add_variant(variant_dto)
        await self.session.commit()

        loaded = await self.variant_repo.get_by_id(new_variant.id)
        return RopeVariantResponseDTO.model_validate(loaded)

    async def get_variants_by_product_id(
        self,
        rope_product_id: int,
        is_active: Optional[bool] = None
    ) -> List[RopeVariantResponseDTO]:
        """Получение всех вариантов товара в порядке index."""
        if not await self.product_repo.exists(rope_product_id):
            raise RopeProductNotFound(
                f"RopeProduct with product_id {rope_product_id} not found."
            )

        items = await self.variant_repo.get_by_product_id(
            rope_product_id=rope_product_id,
            is_active=is_active,
        )
        return [RopeVariantResponseDTO.model_validate(i) for i in items]

    async def get_variant_by_id(self, variant_id: int) -> RopeVariantResponseDTO:
        """Получение варианта по ID."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"RopeVariant with id {variant_id} not found."
            )
        return RopeVariantResponseDTO.model_validate(item)

    async def update_variant(
        self,
        variant_id: int,
        data: RopeVariantUpdate
    ) -> RopeVariantResponseDTO:
        """Обновление характеристик варианта."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"RopeVariant with id {variant_id} not found."
            )

        if data.diameter_mm is not None and data.diameter_mm != float(item.diameter_mm):
            existing = await self.variant_repo.get_by_product_and_diameter(
                rope_product_id=item.rope_product_id,
                diameter_mm=data.diameter_mm,
            )
            if existing and existing.id != variant_id:
                raise RopeVariantAlreadyExists(
                    f"Variant with diameter {data.diameter_mm} mm already exists for RopeProduct {item.rope_product_id}."
                )

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            raise NoDataForUpdate("Did not transmit data")

        await self.variant_repo.update_variant(variant_id, update_dict)
        await self.session.commit()

        updated = await self.variant_repo.get_by_id(variant_id)
        return RopeVariantResponseDTO.model_validate(updated)

    async def reorder_variant(
        self,
        variant_id: int,
        data: RopeVariantUpdateIndexDTO
    ) -> RopeVariantResponseDTO:
        """Изменение позиции варианта внутри товара со сдвигом остальных."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"RopeVariant with id {variant_id} not found."
            )

        if item.index != data.new_index:
            await self.variant_repo.reorder_index(
                obj_id=variant_id,
                old_index=item.index,
                new_index=data.new_index,
                rope_product_id=item.rope_product_id,
            )
            await self.session.commit()

        updated = await self.variant_repo.get_by_id(variant_id)
        return RopeVariantResponseDTO.model_validate(updated)

    async def delete_variant(self, variant_id: int) -> None:
        """Удаление варианта и сдвиг оставшихся индексов для устранения пробелов."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"RopeVariant with id {variant_id} not found."
            )

        deleted_index = item.index
        product_id = item.rope_product_id

        await self.variant_repo.delete_variant(variant_id)
        await self.variant_repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            rope_product_id=product_id,
        )
        await self.session.commit()
