from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from src.modules.products.models import Product
from src.modules.material_groups.models import MaterialGroup
from src.modules.rope_products.models import RopeConfiguratorSetting, ProductVariant
from tests.modules.splice_materials.fixtures.factory import create_splice_material_factory


async def create_rope_product_factory(
    session_db: AsyncSession,
    new_product: CreateRopeProductFixtureDTO = CreateRopeProductFixtureDTO(),
) -> RopeConfiguratorSetting:
    if new_product.product_id is None:
        product = Product()
        session_db.add(product)
        await session_db.flush()
        product_id = product.id
    else:
        product_id = new_product.product_id

    if new_product.material_group_id is None:
        mg = MaterialGroup(
            code=random_string(),
            index=1,
            is_active=True,
        )
        session_db.add(mg)
        await session_db.flush()
        material_group_id = mg.id
    else:
        material_group_id = new_product.material_group_id

    if new_product.splice_material_id is None:
        sm = await create_splice_material_factory(session_db=session_db)
        splice_material_id = sm.id
    else:
        splice_material_id = new_product.splice_material_id

    setting = RopeConfiguratorSetting(
        product_id=product_id,
        material_group_id=material_group_id,
        material_id=new_product.material_id,
        splice_material_id=splice_material_id,
        construction=new_product.construction or "Double Braid",
        core_description=new_product.core_description,
        cover_description=new_product.cover_description,
        can_be_spliced=True if new_product.can_be_spliced is None else new_product.can_be_spliced,
    )
    session_db.add(setting)
    await session_db.commit()
    await session_db.refresh(setting)

    return setting


async def create_rope_variant_factory(
    session_db: AsyncSession,
    new_variant: CreateRopeVariantFixtureDTO = CreateRopeVariantFixtureDTO(),
) -> ProductVariant:
    if new_variant.product_id is None:
        rp = await create_rope_product_factory(session_db=session_db)
        product_id = rp.product_id
    else:
        product_id = new_variant.product_id

    variant_name = new_variant.variant_name or "10 мм"
    size_value = new_variant.size_value if new_variant.size_value is not None else 10.0
    price = new_variant.price if new_variant.price is not None else 5.0

    if new_variant.index is None:
        stmt = select(func.coalesce(func.max(ProductVariant.index), 0)).where(
            ProductVariant.product_id == product_id
        )
        max_idx = (await session_db.execute(stmt)).scalar_one()
        index = max_idx + 1
    else:
        index = new_variant.index

    variant = ProductVariant(
        product_id=product_id,
        variant_name=variant_name,
        size_value=size_value,
        breaking_load_dan=new_variant.breaking_load_dan,
        working_load_dan=new_variant.working_load_dan,
        working_stretch_percent=new_variant.working_stretch_percent,
        weight_g=new_variant.weight_g,
        price=price,
        sku=new_variant.sku,
        index=index,
        is_active=True if new_variant.is_active is None else new_variant.is_active,
    )
    session_db.add(variant)
    await session_db.commit()
    await session_db.refresh(variant)

    return variant
