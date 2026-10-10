from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.material_groups.fixtures.models_dto import (
    CreateMaterialGroupFixtureDTO,
    CreateMaterialGroupTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.material_groups.models import MaterialGroup, MaterialGroupTranslation
from src.modules.material_groups.models_dto import (
    MaterialGroupResponseDTO,
    MaterialGroupTranslationResponseDTO,
)


async def create_material_group_factory(
    session_db: AsyncSession,
    new_group: CreateMaterialGroupFixtureDTO = CreateMaterialGroupFixtureDTO(),
) -> MaterialGroupResponseDTO:
    if new_group.index is None:
        stmt = select(func.coalesce(func.max(MaterialGroup.index), 0))
        max_idx = (await session_db.execute(stmt)).scalar_one()
        index = max_idx + 1
    else:
        index = new_group.index

    group = MaterialGroup(
        code=random_string() if new_group.code is None else new_group.code,
        index=index,
        is_active=True if new_group.is_active is None else new_group.is_active,
    )
    session_db.add(group)
    await session_db.flush()

    # Создаем дефолтный перевод (ENG)
    trans = MaterialGroupTranslation(
        material_group_id=group.id,
        locale=new_group.locale if new_group.locale is not None else Language.ENG,
        name=new_group.name if new_group.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(MaterialGroup)
        .options(selectinload(MaterialGroup.translations))
        .where(MaterialGroup.id == group.id)
    )
    loaded_group = result.scalar_one()

    return MaterialGroupResponseDTO.model_validate(loaded_group)


async def create_material_group_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateMaterialGroupTranslationFixtureDTO = CreateMaterialGroupTranslationFixtureDTO(),
) -> MaterialGroupTranslationResponseDTO:
    if new_trans.material_group_id is None:
        group_dto = await create_material_group_factory(session_db=session_db)
        material_group_id = group_dto.id
    else:
        material_group_id = new_trans.material_group_id

    trans = MaterialGroupTranslation(
        material_group_id=material_group_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return MaterialGroupTranslationResponseDTO.model_validate(trans)
