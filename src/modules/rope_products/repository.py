from typing import Optional, Sequence

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository, BaseIndexedRepository
from src.modules.products.models import Product
from src.modules.material_groups.models import MaterialGroup
from src.modules.materials.models import Material
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant
from src.modules.rope_product_color.models import ProductColor
from src.modules.colors.models import Color
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.splice_types.models import SpliceType
from src.modules.rope_products.models_dto import (
    RopeConfiguratorSettingBase,
    RopeConfiguratorSettingUpdate,
    ProductVariantBase,
    ProductVariantUpdate,
)


class RopeProductRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=RopeConfiguratorSetting)

    async def add_setting(self, data: RopeConfiguratorSettingBase) -> RopeConfiguratorSetting:
        """Добавление конфигурационных настроек для товара-каната."""
        return self.add(data.model_dump())

    async def create_base_product(self) -> Product:
        """Создание базового объекта Product в таблице products."""
        product = Product(product_type="rope")
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_by_id(
        self,
        product_id: int,
        include_relations: bool = False
    ) -> RopeConfiguratorSetting | None:
        """Получение настроек каната по ID."""
        stmt = select(RopeConfiguratorSetting).where(RopeConfiguratorSetting.product_id == product_id)
        if include_relations:
            stmt = stmt.options(
                selectinload(RopeConfiguratorSetting.product).selectinload(Product.translations),
                selectinload(RopeConfiguratorSetting.product).selectinload(Product.variants),
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.colors)
                .selectinload(ProductColor.color)
                .selectinload(Color.translations),
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.allowed_splices)
                .selectinload(RopeAllowedSplice.splice_type)
                .selectinload(SpliceType.translations),
                selectinload(RopeConfiguratorSetting.material_group).selectinload(MaterialGroup.translations),
                selectinload(RopeConfiguratorSetting.material).selectinload(Material.translations),
                selectinload(RopeConfiguratorSetting.splice_material),
            )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        material_group_id: Optional[int] = None,
        can_be_spliced: Optional[bool] = None
    ) -> Sequence[RopeConfiguratorSetting]:
        """Получение списка всех настроек канатов с фильтрацией."""
        stmt = select(RopeConfiguratorSetting)
        if material_group_id is not None:
            stmt = stmt.where(RopeConfiguratorSetting.material_group_id == material_group_id)
        if can_be_spliced is not None:
            stmt = stmt.where(RopeConfiguratorSetting.can_be_spliced == can_be_spliced)
        stmt = stmt.order_by(RopeConfiguratorSetting.product_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def exists(self, product_id: int) -> bool:
        """Проверка существования настроек каната."""
        stmt = select(exists().where(RopeConfiguratorSetting.product_id == product_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_base_product(self, product_id: int) -> bool:
        """Проверка существования базового Product."""
        stmt = select(exists().where(Product.id == product_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_material_group(self, material_group_id: int) -> bool:
        """Проверка существования группы материалов."""
        stmt = select(exists().where(MaterialGroup.id == material_group_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_material(self, material_id: int) -> bool:
        """Проверка существования конкретного материала."""
        stmt = select(exists().where(Material.id == material_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def exists_splice_material(self, splice_material_id: int) -> bool:
        """Проверка существования материала сращивания."""
        stmt = select(exists().where(SpliceMaterial.id == splice_material_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def has_dependencies(self, product_id: int) -> bool:
        """Проверка наличия связей (варианты, цвета, разрешенные сплайсы)."""
        variants_exist_stmt = select(exists().where(ProductVariant.product_id == product_id))
        colors_exist_stmt = select(exists().where(ProductColor.product_id == product_id))
        splices_exist_stmt = select(exists().where(RopeAllowedSplice.product_id == product_id))

        has_variants = await self.session.scalar(variants_exist_stmt)
        has_colors = await self.session.scalar(colors_exist_stmt)
        has_splices = await self.session.scalar(splices_exist_stmt)

        return bool(has_variants or has_colors or has_splices)

    async def update_setting(self, product_id: int, data: RopeConfiguratorSettingUpdate) -> None:
        """Обновление настроек товара-каната."""
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            stmt = (
                update(RopeConfiguratorSetting)
                .where(RopeConfiguratorSetting.product_id == product_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)

    async def delete_setting(self, product_id: int) -> None:
        """Удаление настроек каната."""
        stmt = delete(RopeConfiguratorSetting).where(RopeConfiguratorSetting.product_id == product_id)
        await self.session.execute(stmt)


class ProductVariantRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ProductVariant)

    async def add_variant(self, data: ProductVariantBase) -> ProductVariant:
        """Добавление варианта товара."""
        return self.add(data.model_dump())

    async def get_by_id(self, variant_id: int) -> ProductVariant | None:
        """Получение варианта по ID."""
        stmt = select(ProductVariant).where(ProductVariant.id == variant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(
        self,
        product_id: int,
        is_active: Optional[bool] = None
    ) -> Sequence[ProductVariant]:
        """Получение всех вариантов товара в порядке возрастания index."""
        stmt = select(ProductVariant).where(ProductVariant.product_id == product_id)
        if is_active is not None:
            stmt = stmt.where(ProductVariant.is_active == is_active)
        stmt = stmt.order_by(ProductVariant.index)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_product_and_size(
        self,
        product_id: int,
        size_value: float
    ) -> ProductVariant | None:
        """Поиск варианта товара по размеру/диаметру."""
        stmt = select(ProductVariant).where(
            ProductVariant.product_id == product_id,
            ProductVariant.size_value == size_value,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_and_name(
        self,
        product_id: int,
        variant_name: str
    ) -> ProductVariant | None:
        """Поиск варианта товара по названию модификации."""
        stmt = select(ProductVariant).where(
            ProductVariant.product_id == product_id,
            ProductVariant.variant_name == variant_name,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_variant(self, variant_id: int, data: ProductVariantUpdate) -> None:
        """Обновление полей варианта."""
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            stmt = (
                update(ProductVariant)
                .where(ProductVariant.id == variant_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)

    async def delete_variant(self, variant_id: int) -> None:
        """Удаление варианта по ID."""
        stmt = delete(ProductVariant).where(ProductVariant.id == variant_id)
        await self.session.execute(stmt)
