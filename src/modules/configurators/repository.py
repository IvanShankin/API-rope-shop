from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.base.repository_model import BaseRepository
from src.modules.configurator_setting.models import ConfiguratorSetting
from src.modules.configurator_extra.models import ConfiguratorExtra, BillingType
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.splice_types.models import SpliceType, SpliceCategory
from src.modules.splice_prices.models import SplicePriceRule
from src.modules.products.models import Product
from src.modules.rope_products.models import RopeConfiguratorSetting
from src.modules.rope_product_color.models import ProductColor
from src.modules.colors.models import Color
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.material_groups.models import MaterialGroup


class ConfiguratorRepository(BaseRepository):
    """Репозиторий агрегированного чтения данных для конфигураторов."""

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ConfiguratorSetting)

    async def get_setting(self) -> Optional[ConfiguratorSetting]:
        """Получение системных настроек конфигуратора."""
        stmt = select(ConfiguratorSetting).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_extras(
        self,
        billing_type: Optional[BillingType] = None,
        is_active: Optional[bool] = True,
    ) -> Sequence[ConfiguratorExtra]:
        """Получение дополнительных опций конфигуратора с переводами."""
        stmt = select(ConfiguratorExtra).options(
            selectinload(ConfiguratorExtra.translations)
        )
        if is_active is not None:
            stmt = stmt.where(ConfiguratorExtra.is_active == is_active)
        if billing_type is not None:
            stmt = stmt.where(ConfiguratorExtra.billing_type == billing_type)
        stmt = stmt.order_by(ConfiguratorExtra.index.asc(), ConfiguratorExtra.id.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_splice_materials(self) -> Sequence[SpliceMaterial]:
        """Получение списка тарифных групп материалов заделок."""
        stmt = select(SpliceMaterial).order_by(SpliceMaterial.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_splice_types(
        self,
        category: Optional[SpliceCategory] = None,
        is_active: Optional[bool] = True,
    ) -> Sequence[SpliceType]:
        """Получение списка услуг заделок (петли / сращивания) с переводами."""
        stmt = select(SpliceType).options(
            selectinload(SpliceType.translations)
        )
        if is_active is not None:
            stmt = stmt.where(SpliceType.is_active == is_active)
        if category is not None:
            stmt = stmt.where(SpliceType.category == category)
        stmt = stmt.order_by(SpliceType.index.asc(), SpliceType.id.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_splice_price_rules(
        self,
        category: Optional[SpliceCategory] = None,
        is_active: Optional[bool] = True,
    ) -> Sequence[SplicePriceRule]:
        """Получение матрицы цен на заделки с опциональной фильтрацией по категории услуги."""
        stmt = select(SplicePriceRule).options(
            selectinload(SplicePriceRule.splice_type).selectinload(SpliceType.translations),
            selectinload(SplicePriceRule.splice_material),
        )
        if category is not None:
            stmt = stmt.join(SplicePriceRule.splice_type).where(SpliceType.category == category)
        if is_active is not None:
            stmt = stmt.where(SplicePriceRule.is_active == is_active)
        stmt = stmt.order_by(SplicePriceRule.diameter_from_mm.asc().nulls_first(), SplicePriceRule.id.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_rope_products(self) -> Sequence[RopeConfiguratorSetting]:
        """Получение каталога канатов со всеми связанными вариантами, цветами и разрешенными заделками."""
        stmt = (
            select(RopeConfiguratorSetting)
            .options(
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.translations),
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.images),
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.variants),
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.colors)
                .selectinload(ProductColor.color)
                .selectinload(Color.translations),
                selectinload(RopeConfiguratorSetting.product)
                .selectinload(Product.allowed_splices)
                .selectinload(RopeAllowedSplice.splice_type)
                .selectinload(SpliceType.translations),
                selectinload(RopeConfiguratorSetting.material_group)
                .selectinload(MaterialGroup.translations),
                selectinload(RopeConfiguratorSetting.splice_material),
            )
            .order_by(RopeConfiguratorSetting.product_id)
        )
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        for item in items:
            if item.product and item.product.variants:
                item.product.variants.sort(key=lambda v: v.index)
        return items
