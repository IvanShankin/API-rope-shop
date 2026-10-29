from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.splice_types.fixtures.models_dto import (
    CreateSpliceTypeFixtureDTO,
    CreateSpliceTypeTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.splice_types.models import SpliceType, SpliceTypeTranslation, SpliceCategory, SpliceVisualType
from src.modules.splice_types.models_dto import (
    SpliceTypeResponseDTO,
    SpliceTypeTranslationResponseDTO,
)


async def create_splice_type_factory(
    session_db: AsyncSession,
    new_type: CreateSpliceTypeFixtureDTO = CreateSpliceTypeFixtureDTO()
) -> SpliceTypeResponseDTO:
    splice_type = SpliceType(
        code=random_string() if new_type.code is None else new_type.code,
        category=SpliceCategory.LOOP if new_type.category is None else new_type.category,
        visual_type=SpliceVisualType.GENERIC if new_type.visual_type is None else new_type.visual_type,
        index=1 if new_type.index is None else new_type.index,
        is_active=True if new_type.is_active is None else new_type.is_active,
        image_url=new_type.image_url,
    )
    session_db.add(splice_type)
    await session_db.flush()

    # Создаем перевод по умолчанию для типа сплайса
    trans = SpliceTypeTranslation(
        splice_type_id=splice_type.id,
        locale=new_type.locale if new_type.locale is not None else Language.ENG,
        name=new_type.name if new_type.name is not None else random_string(),
        description=new_type.description if new_type.description is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(SpliceType).where(SpliceType.id == splice_type.id).options(selectinload(SpliceType.translations))
    )
    splice_type = result.scalar_one()

    return SpliceTypeResponseDTO.model_validate(splice_type)


async def create_splice_type_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateSpliceTypeTranslationFixtureDTO = CreateSpliceTypeTranslationFixtureDTO()
) -> SpliceTypeTranslationResponseDTO:
    if new_trans.splice_type_id is None:
        st = await create_splice_type_factory(session_db=session_db)
        splice_type_id = st.id
    else:
        splice_type_id = new_trans.splice_type_id

    trans = SpliceTypeTranslation(
        splice_type_id=splice_type_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
        description=new_trans.description if new_trans.description is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return SpliceTypeTranslationResponseDTO.model_validate(trans)
