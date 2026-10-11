from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.rope_products.fixtures.models_dto import (
    CreateRopeProductFixtureDTO,
    CreateRopeVariantFixtureDTO,
)
from src.modules.products.models import Product
from src.modules.material_groups.models import MaterialGroup
from src.modules.rope_products.models import RopeProduct, RopeVariant
from tests.modules.splice_materials.fixtures.factory import create_splice_material_factory


async def create_rope_product_factory(
    session_db: AsyncSession,
    new_product: CreateRopeProductFixtureDTO = CreateRopeProductFixtureDTO(),
) -> RopeProduct:
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

    rope_product = RopeProduct(
        product_id=product_id,
        material_group_id=material_group_id,
        splice_material_id=splice_material_id,
        construction=new_product.construction or "Double Braid",
        core_description=new_product.core_description,
        cover_description=new_product.cover_description,
        working_stretch_percent=new_product.working_stretch_percent,
        can_be_spliced=True if new_product.can_be_spliced is None else new_product.can_be_spliced,
    )
    session_db.add(rope_product)
    await session_db.commit()
    await session_db.refresh(rope_product)

    return rope_product


async def create_rope_variant_factory(
    session_db: AsyncSession,
    new_variant: CreateRopeVariantFixtureDTO = CreateRopeVariantFixtureDTO(),
) -> RopeVariant:
    if new_variant.rope_product_id is None:
        rp = await create_rope_product_factory(session_db=session_db)
        rope_product_id = rp.product_id
    else:
        rope_product_id = new_variant.rope_product_id

    diameter_mm = 10.0 if new_variant.diameter_mm is None else new_variant.diameter_mm
    price_per_meter = 5.0 if new_variant.price_per_meter is None else new_variant.price_per_meter

    if new_variant.index is None:
        stmt = select(func.coalesce(func.max(RopeVariant.index), 0)).where(
            RopeVariant.rope_product_id == rope_product_id
        )
        max_idx = (await session_db.execute(stmt)).scalar_one()
        index = max_idx + 1
    else:
        index = new_variant.index

    variant = RopeVariant(
        rope_product_id=rope_product_id,
        diameter_mm=diameter_mm,
        breaking_load_dan=new_variant.breaking_load_dan,
        weight_g_per_m=new_variant.weight_g_per_m,
        price_per_meter=price_per_meter,
        index=index,
        is_active=True if new_variant.is_active is None else new_variant.is_active,
    )
    session_db.add(variant)
    await session_db.commit()
    await session_db.refresh(variant)

    return variant
