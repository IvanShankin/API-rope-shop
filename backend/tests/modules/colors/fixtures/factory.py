from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from tests.helpers.functions import random_string
from tests.modules.colors.fixtures.models_dto import (
    CreateColorFixtureDTO,
    CreateColorTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.colors.models import Color, ColorTranslation
from src.modules.colors.models_dto import (
    ColorResponseDTO,
    ColorTranslationResponseDTO,
)


async def create_color_factory(
    session_db: AsyncSession,
    new_color: CreateColorFixtureDTO = CreateColorFixtureDTO()
) -> ColorResponseDTO:
    color = Color(
        code=random_string() if new_color.code is None else new_color.code,
        hex="#FF0000" if new_color.hex is None else new_color.hex,
        index=1 if new_color.index is None else new_color.index,
        is_active=True if new_color.is_active is None else new_color.is_active,
    )
    session_db.add(color)
    await session_db.flush()

    # Default translation
    trans = ColorTranslation(
        color_id=color.id,
        locale=new_color.locale if new_color.locale is not None else Language.ENG,
        name=new_color.name if new_color.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(Color).where(Color.id == color.id).options(selectinload(Color.translations))
    )
    color = result.scalar_one()

    return ColorResponseDTO.model_validate(color)


async def create_color_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateColorTranslationFixtureDTO = CreateColorTranslationFixtureDTO()
) -> ColorTranslationResponseDTO:
    if new_trans.color_id is None:
        c = await create_color_factory(session_db=session_db)
        color_id = c.id
    else:
        color_id = new_trans.color_id

    trans = ColorTranslation(
        color_id=color_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return ColorTranslationResponseDTO.model_validate(trans)
