from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.rope_product_color.fixtures.models_dto import CreateRopeProductColorFixtureDTO
from src.modules.colors.models import Color
from src.modules.rope_product_color.models import ProductColor
from src.modules.rope_product_color.models_dto import ProductColorResponseDTO
from tests.modules.rope_products.fixtures.factory import create_rope_product_factory
from tests.modules.colors.fixtures.factory import create_color_factory


async def create_rope_product_color_factory(
    session_db: AsyncSession,
    new_item: CreateRopeProductColorFixtureDTO = CreateRopeProductColorFixtureDTO(),
) -> ProductColorResponseDTO:
    if new_item.product_id is None:
        rp = await create_rope_product_factory(session_db=session_db)
        product_id = rp.product_id
    else:
        product_id = new_item.product_id

    if new_item.color_id is None:
        c = await create_color_factory(session_db=session_db)
        color_id = c.id
    else:
        color_id = new_item.color_id

    if new_item.index is None:
        stmt = select(func.coalesce(func.max(ProductColor.index), 0)).where(
            ProductColor.product_id == product_id
        )
        max_idx = (await session_db.execute(stmt)).scalar_one()
        index = max_idx + 1
    else:
        index = new_item.index

    item = ProductColor(
        product_id=product_id,
        color_id=color_id,
        index=index,
    )
    session_db.add(item)
    await session_db.commit()

    stmt = (
        select(ProductColor)
        .options(
            selectinload(ProductColor.color)
            .selectinload(Color.translations)
        )
        .where(ProductColor.id == item.id)
    )
    loaded = (await session_db.execute(stmt)).scalar_one()

    return ProductColorResponseDTO.model_validate(loaded)
