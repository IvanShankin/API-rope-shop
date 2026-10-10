from typing import Optional, Sequence, Union, Any

from sqlalchemy import select, update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository, BaseIndexedRepository
from src.modules.products.models import Product
from src.modules.material_groups.models import MaterialGroup
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.rope_products.models import RopeProduct, RopeVariant
from src.modules.rope_product_color.models import RopeProductColor
from src.modules.colors.models import Color
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.splice_types.models import SpliceType


class RopeProductRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=RopeProduct)

    async def add_product(self, data: Union[dict, Any]) -> RopeProduct:
        """Добавление нового товара-веревки."""
        return self.add(data)

    async def create_base_product(self) -> Product:
        """Создание базового объекта Product в таблице products."""
        product = Product()
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_by_id(
        self,
        product_id: int,
        include_relations: bool = False
    ) -> RopeProduct | None:
        """Получение товара-веревки по ID (с опциональной предзагрузкой связей)."""
        stmt = select(RopeProduct).where(RopeProduct.product_id == product_id)
        if include_relations:
            stmt = stmt.options(
                selectinload(RopeProduct.variants),
                selectinload(RopeProduct.colors)
                .selectinload(RopeProductColor.color)
                .selectinload(Color.translations),
                selectinload(RopeProduct.allowed_splices)
                .selectinload(RopeAllowedSplice.splice_type)
                .selectinload(SpliceType.translations),
                selectinload(RopeProduct.material_group),
                selectinload(RopeProduct.splice_material),
            )
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()
        if item and include_relations and item.variants:
            item.variants.sort(key=lambda v: v.index)
        return item

    async def get_all(
        self,
        material_group_id: Optional[int] = None,
        can_be_spliced: Optional[bool] = None
    ) -> Sequence[RopeProduct]:
        """Получение списка всех товаров-веревок с фильтрацией."""
        stmt = select(RopeProduct)
        if material_group_id is not None:
            stmt = stmt.where(RopeProduct.material_group_id == material_group_id)
        if can_be_spliced is not None:
            stmt = stmt.where(RopeProduct.can_be_spliced == can_be_spliced)
        stmt = stmt.order_by(RopeProduct.product_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def exists(self, product_id: int) -> bool:
        """Проверка существования товара-веревки."""
        stmt = select(exists().where(RopeProduct.product_id == product_id))
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

    async def exists_splice_material(self, splice_material_id: int) -> bool:
        """Проверка существования материала сращивания."""
        stmt = select(exists().where(SpliceMaterial.id == splice_material_id))
        result = await self.session.scalar(stmt)
        return bool(result)

    async def has_dependencies(self, product_id: int) -> bool:
        """Проверка наличия связей (варианты, цвета, разрешенные сплайсы)."""
        variants_exist_stmt = select(exists().where(RopeVariant.rope_product_id == product_id))
        colors_exist_stmt = select(exists().where(RopeProductColor.rope_product_id == product_id))
        splices_exist_stmt = select(exists().where(RopeAllowedSplice.rope_product_id == product_id))

        has_variants = await self.session.scalar(variants_exist_stmt)
        has_colors = await self.session.scalar(colors_exist_stmt)
        has_splices = await self.session.scalar(splices_exist_stmt)

        return bool(has_variants or has_colors or has_splices)

    async def update_product(self, product_id: int, update_data: dict) -> None:
        """Обновление полей товара-веревки."""
        stmt = (
            update(RopeProduct)
            .where(RopeProduct.product_id == product_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_product(self, product_id: int) -> None:
        """Удаление товара-веревки."""
        stmt = delete(RopeProduct).where(RopeProduct.product_id == product_id)
        await self.session.execute(stmt)


class RopeVariantRepository(BaseIndexedRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=RopeVariant)

    async def add_variant(self, data: Union[dict, Any]) -> RopeVariant:
        """Добавление диаметра/варианта товара."""
        return self.add(data)

    async def get_by_id(self, variant_id: int) -> RopeVariant | None:
        """Получение варианта по ID."""
        stmt = select(RopeVariant).where(RopeVariant.id == variant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(
        self,
        rope_product_id: int,
        is_active: Optional[bool] = None
    ) -> Sequence[RopeVariant]:
        """Получение всех вариантов товара в порядке возрастания index."""
        stmt = select(RopeVariant).where(RopeVariant.rope_product_id == rope_product_id)
        if is_active is not None:
            stmt = stmt.where(RopeVariant.is_active == is_active)
        stmt = stmt.order_by(RopeVariant.index)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_product_and_diameter(
        self,
        rope_product_id: int,
        diameter_mm: float
    ) -> RopeVariant | None:
        """Поиск варианта товара по диаметру."""
        stmt = select(RopeVariant).where(
            RopeVariant.rope_product_id == rope_product_id,
            RopeVariant.diameter_mm == diameter_mm,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_variant(self, variant_id: int, update_data: dict) -> None:
        """Обновление полей варианта."""
        stmt = (
            update(RopeVariant)
            .where(RopeVariant.id == variant_id)
            .values(**update_data)
        )
        await self.session.execute(stmt)

    async def delete_variant(self, variant_id: int) -> None:
        """Удаление варианта по ID."""
        stmt = delete(RopeVariant).where(RopeVariant.id == variant_id)
        await self.session.execute(stmt)
