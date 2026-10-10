from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.rope_allowed_splice.fixtures.models_dto import CreateRopeAllowedSpliceFixtureDTO
from src.modules.splice_types.models import SpliceType
from src.modules.rope_allowed_splice.models import RopeAllowedSplice
from src.modules.rope_allowed_splice.models_dto import RopeAllowedSpliceResponseDTO
from tests.modules.rope_products.fixtures.factory import create_rope_product_factory
from tests.modules.splice_types.fixtures.factory import create_splice_type_factory


async def create_rope_allowed_splice_factory(
    session_db: AsyncSession,
    new_item: CreateRopeAllowedSpliceFixtureDTO = CreateRopeAllowedSpliceFixtureDTO(),
) -> RopeAllowedSpliceResponseDTO:
    if new_item.rope_product_id is None:
        rp = await create_rope_product_factory(session_db=session_db)
        rope_product_id = rp.product_id
    else:
        rope_product_id = new_item.rope_product_id

    if new_item.splice_type_id is None:
        st = await create_splice_type_factory(session_db=session_db)
        splice_type_id = st.id
    else:
        splice_type_id = new_item.splice_type_id

    item = RopeAllowedSplice(
        rope_product_id=rope_product_id,
        splice_type_id=splice_type_id,
    )
    session_db.add(item)
    await session_db.commit()

    stmt = (
        select(RopeAllowedSplice)
        .options(
            selectinload(RopeAllowedSplice.splice_type)
            .selectinload(SpliceType.translations)
        )
        .where(
            RopeAllowedSplice.rope_product_id == rope_product_id,
            RopeAllowedSplice.splice_type_id == splice_type_id,
        )
    )
    loaded = (await session_db.execute(stmt)).scalar_one()

    return RopeAllowedSpliceResponseDTO.model_validate(loaded)
