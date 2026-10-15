from typing import Optional, List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.products.models import Product
from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant
from src.modules.rope_products.repository import RopeProductRepository, ProductVariantRepository
from src.modules.material_groups.repository import MaterialGroupRepository
from src.modules.materials.repository import MaterialRepository
from src.modules.splice_materials.repository import SpliceMaterialRepository
from src.modules.rope_products.models_dto import (
    RopeConfiguratorSettingCreate,
    RopeConfiguratorSettingUpdate,
    RopeConfiguratorSettingResponseDTO,
    RopeConfiguratorSettingDetailResponseDTO,
    RopeConfiguratorSettingBase,
    ProductVariantCreate,
    ProductVariantCreateForProduct,
    ProductVariantUpdate,
    ProductVariantUpdateIndexDTO,
    ProductVariantResponseDTO,
    ProductVariantBase,
)
from src.modules.rope_products.exception import (
    RopeProductNotFound,
    RopeProductAlreadyExists,
    RopeProductHasDependencies,
    RopeVariantNotFound,
    RopeVariantAlreadyExists,
    MaterialGroupNotFound,
    MaterialNotFound,
    SpliceMaterialNotFound,
)
from src.modules.rope_product_color.models_dto import ProductColorResponseDTO
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceResponseDTO
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO


class RopeProductsService:
    def __init__(
        self,
        product_repo: RopeProductRepository,
        variant_repo: ProductVariantRepository,
        material_group_repo: MaterialGroupRepository,
        material_repo: MaterialRepository,
        splice_material_repo: SpliceMaterialRepository,
        session: AsyncSession,
    ):
        self.product_repo = product_repo
        self.variant_repo = variant_repo
        self.material_group_repo = material_group_repo
        self.material_repo = material_repo
        self.splice_material_repo = splice_material_repo
        self.session = session

    # ==================== RopeConfiguratorSetting Operations ====================

    async def create_rope_product(
        self,
        data: RopeConfiguratorSettingCreate
    ) -> RopeConfiguratorSettingResponseDTO:
        """Создание конфигурационных настроек для товара-каната."""
        if not await self.material_group_repo.get_by_group_id(data.material_group_id):
            raise MaterialGroupNotFound(
                f"MaterialGroup with id {data.material_group_id} not found."
            )

        if data.material_id is not None:
            if not await self.material_repo.exists_material(data.material_id):
                raise MaterialNotFound(
                    f"Material with id {data.material_id} not found."
                )

        if not await self.splice_material_repo.get_by_id(data.splice_material_id):
            raise SpliceMaterialNotFound(
                f"SpliceMaterial with id {data.splice_material_id} not found."
            )

        if data.product_id is not None:
            if await self.product_repo.exists(data.product_id):
                raise RopeProductAlreadyExists(
                    f"RopeConfiguratorSetting with product_id {data.product_id} already exists."
                )
            if not await self.product_repo.exists_base_product(data.product_id):
                base_product = Product(id=data.product_id, product_type="rope")
                self.session.add(base_product)
                await self.session.flush()
            target_product_id = data.product_id
        else:
            base_product = await self.product_repo.create_base_product()
            target_product_id = base_product.id

        setting_dto = RopeConfiguratorSettingBase(
            product_id=target_product_id,
            material_group_id=data.material_group_id,
            material_id=data.material_id,
            splice_material_id=data.splice_material_id,
            construction=data.construction,
            core_description=data.core_description,
            cover_description=data.cover_description,
            can_be_spliced=data.can_be_spliced,
        )

        new_setting = await self.product_repo.add_setting(setting_dto)
        await self.session.commit()

        loaded = await self.product_repo.get_by_id(new_setting.product_id)
        return RopeConfiguratorSettingResponseDTO.model_validate(loaded)

    async def get_rope_product(
        self,
        product_id: int
    ) -> RopeConfiguratorSettingDetailResponseDTO:
        """Получение детальной информации о настройках каната."""
        item = await self.product_repo.get_by_id(product_id, include_relations=True)
        if not item:
            raise RopeProductNotFound(
                f"RopeConfiguratorSetting with product_id {product_id} not found."
            )

        variants = []
        colors = []
        allowed_splices = []

        if item.product:
            if item.product.variants:
                variants = [ProductVariantResponseDTO.model_validate(v) for v in item.product.variants]
            if item.product.colors:
                colors = [ProductColorResponseDTO.model_validate(c) for c in item.product.colors]
            if item.product.allowed_splices:
                allowed_splices = [RopeAllowedSpliceResponseDTO.model_validate(s) for s in item.product.allowed_splices]

        splice_material = None
        if item.splice_material:
            splice_material = SpliceMaterialResponseDTO.model_validate(item.splice_material)

        return RopeConfiguratorSettingDetailResponseDTO(
            product_id=item.product_id,
            material_group_id=item.material_group_id,
            material_id=item.material_id,
            splice_material_id=item.splice_material_id,
            construction=item.construction,
            core_description=item.core_description,
            cover_description=item.cover_description,
            can_be_spliced=item.can_be_spliced,
            created_at=item.created_at,
            updated_at=item.updated_at,
            variants=variants,
            colors=colors,
            allowed_splices=allowed_splices,
            splice_material=splice_material,
        )

    async def get_all_rope_products(
        self,
        material_group_id: Optional[int] = None,
        can_be_spliced: Optional[bool] = None,
    ) -> Sequence[RopeConfiguratorSettingResponseDTO]:
        """Получение списка товаров-веревок с фильтрацией."""
        items = await self.product_repo.get_all(
            material_group_id=material_group_id,
            can_be_spliced=can_be_spliced,
        )
        return [RopeConfiguratorSettingResponseDTO.model_validate(item) for item in items]

    async def update_rope_product(
        self,
        product_id: int,
        data: RopeConfiguratorSettingUpdate
    ) -> RopeConfiguratorSettingResponseDTO:
        """Обновление характеристик товара-веревки."""
        if not await self.product_repo.exists(product_id):
            raise RopeProductNotFound(
                f"RopeConfiguratorSetting with product_id {product_id} not found."
            )

        if data.material_group_id is not None:
            if not await self.material_group_repo.get_by_group_id(data.material_group_id):
                raise MaterialGroupNotFound(
                    f"MaterialGroup with id {data.material_group_id} not found."
                )

        if data.material_id is not None:
            if not await self.material_repo.exists_material(data.material_id):
                raise MaterialNotFound(
                    f"Material with id {data.material_id} not found."
                )

        if data.splice_material_id is not None:
            if not await self.splice_material_repo.get_by_id(data.splice_material_id):
                raise SpliceMaterialNotFound(
                    f"SpliceMaterial with id {data.splice_material_id} not found."
                )

        await self.product_repo.update_setting(product_id, data)
        await self.session.commit()

        updated = await self.product_repo.get_by_id(product_id)
        return RopeConfiguratorSettingResponseDTO.model_validate(updated)

    async def delete_rope_product(self, product_id: int) -> None:
        """Удаление товара-веревки с проверкой зависимостей."""
        if not await self.product_repo.exists(product_id):
            raise RopeProductNotFound(
                f"RopeConfiguratorSetting with product_id {product_id} not found."
            )

        if await self.product_repo.has_dependencies(product_id):
            raise RopeProductHasDependencies(
                f"Cannot delete RopeConfiguratorSetting {product_id}: it has associated variants, colors, or splices."
            )

        await self.product_repo.delete_setting(product_id)
        await self.session.commit()

    # ==================== ProductVariant Operations ====================

    async def create_variant(
        self,
        data: ProductVariantCreate
    ) -> ProductVariantResponseDTO:
        """Добавление варианта товара."""
        if not await self.product_repo.exists_base_product(data.product_id):
            raise RopeProductNotFound(
                f"Product with id {data.product_id} not found."
            )

        if data.size_value is not None:
            existing = await self.variant_repo.get_by_product_and_size(
                product_id=data.product_id,
                size_value=data.size_value,
            )
            if existing:
                raise RopeVariantAlreadyExists(
                    f"Variant with size {data.size_value} already exists for Product {data.product_id}."
                )

        max_index = await self.variant_repo.get_max_index(
            product_id=data.product_id
        )
        target_index = max_index + 1

        variant_dto = ProductVariantBase(
            product_id=data.product_id,
            variant_name=data.variant_name,
            size_value=data.size_value,
            breaking_load_dan=data.breaking_load_dan,
            working_load_dan=data.working_load_dan,
            working_stretch_percent=data.working_stretch_percent,
            weight_g=data.weight_g,
            price=data.price,
            sku=data.sku,
            index=target_index,
            is_active=data.is_active,
        )

        new_variant = await self.variant_repo.add_variant(variant_dto)
        await self.session.commit()

        loaded = await self.variant_repo.get_by_id(new_variant.id)
        return ProductVariantResponseDTO.model_validate(loaded)

    async def create_variant_for_product(
        self,
        product_id: int,
        data: ProductVariantCreateForProduct
    ) -> ProductVariantResponseDTO:
        """Добавление варианта для указанного товара."""
        full_create = ProductVariantCreate(
            product_id=product_id,
            variant_name=data.variant_name,
            size_value=data.size_value,
            breaking_load_dan=data.breaking_load_dan,
            working_load_dan=data.working_load_dan,
            working_stretch_percent=data.working_stretch_percent,
            weight_g=data.weight_g,
            price=data.price,
            sku=data.sku,
            is_active=data.is_active,
        )
        return await self.create_variant(full_create)

    async def get_variants_for_product(
        self,
        product_id: int,
        is_active: Optional[bool] = None
    ) -> Sequence[ProductVariantResponseDTO]:
        """Получение списка вариантов товара."""
        if not await self.product_repo.exists_base_product(product_id):
            raise RopeProductNotFound(
                f"Product with id {product_id} not found."
            )
        items = await self.variant_repo.get_by_product_id(product_id, is_active=is_active)
        return [ProductVariantResponseDTO.model_validate(item) for item in items]

    async def get_variant_by_id(self, variant_id: int) -> ProductVariantResponseDTO:
        """Получение варианта по ID."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"ProductVariant with id {variant_id} not found."
            )
        return ProductVariantResponseDTO.model_validate(item)

    async def update_variant(
        self,
        variant_id: int,
        data: ProductVariantUpdate
    ) -> ProductVariantResponseDTO:
        """Обновление характеристик варианта."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"ProductVariant with id {variant_id} not found."
            )

        if data.size_value is not None and data.size_value != item.size_value:
            existing = await self.variant_repo.get_by_product_and_size(
                product_id=item.product_id,
                size_value=data.size_value,
            )
            if existing and existing.id != variant_id:
                raise RopeVariantAlreadyExists(
                    f"Variant with size {data.size_value} already exists for product {item.product_id}."
                )

        await self.variant_repo.update_variant(variant_id, data)
        await self.session.commit()

        updated = await self.variant_repo.get_by_id(variant_id)
        return ProductVariantResponseDTO.model_validate(updated)

    async def delete_variant(self, variant_id: int) -> None:
        """Удаление варианта."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"ProductVariant with id {variant_id} not found."
            )

        deleted_index = item.index
        product_id = item.product_id

        await self.variant_repo.delete_variant(variant_id)
        await self.variant_repo.shift_indexes_after_delete(
            deleted_index=deleted_index,
            product_id=product_id,
        )
        await self.session.commit()

    async def update_variant_index(
        self,
        variant_id: int,
        data: ProductVariantUpdateIndexDTO
    ) -> List[ProductVariantResponseDTO]:
        """Изменение позиции варианта в списке."""
        item = await self.variant_repo.get_by_id(variant_id)
        if not item:
            raise RopeVariantNotFound(
                f"ProductVariant with id {variant_id} not found."
            )

        if item.index != data.new_index:
            await self.variant_repo.reorder_index(
                obj_id=variant_id,
                old_index=item.index,
                new_index=data.new_index,
                product_id=item.product_id,
            )
            await self.session.commit()

        all_variants = await self.variant_repo.get_by_product_id(item.product_id)
        return [ProductVariantResponseDTO.model_validate(v) for v in all_variants]
