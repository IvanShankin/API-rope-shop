from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.rope_products.fixtures.models_dto import CreateRopeProductFixtureDTO
from src.modules.products.models import Product
from src.modules.material_groups.models import MaterialGroup
from src.modules.rope_products.models import RopeProduct
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
        can_be_spliced=True if new_product.can_be_spliced is None else new_product.can_be_spliced,
    )
    session_db.add(rope_product)
    await session_db.commit()
    await session_db.refresh(rope_product)

    return rope_product
