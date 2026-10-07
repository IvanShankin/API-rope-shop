from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.splice_types.fixtures.models_dto import CreateSpliceTypeFixtureDTO
from src.modules.splice_types.models import SpliceType, SpliceCategory, SpliceVisualType
from src.modules.splice_types.models_dto import SpliceTypeResponseDTO

async def create_splice_type_factory(
    session_db: AsyncSession,
    new_type: CreateSpliceTypeFixtureDTO = CreateSpliceTypeFixtureDTO()
) -> SpliceTypeResponseDTO:
    splice_type = SpliceType(
        code=random_string() if new_type.code is None else new_type.code,
        category=SpliceCategory.LOOP if new_type.category is None else new_type.category,
        visual_type=SpliceVisualType.GENERIC if new_type.visual_type is None else new_type.visual_type,
        index=1 if new_type.index is None else new_type.index
    )
    session_db.add(splice_type)
    await session_db.commit()
    await session_db.refresh(splice_type)
    
    result = await session_db.execute(
        select(SpliceType).where(SpliceType.id == splice_type.id).options(selectinload(SpliceType.translations))
    )
    splice_type = result.scalar_one()

    return SpliceTypeResponseDTO.model_validate(splice_type)
