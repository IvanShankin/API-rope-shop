from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.material_groups.fixtures.factory import create_material_group_factory
from tests.modules.materials.fixtures.models_dto import (
    CreateMaterialFixtureDTO,
    CreateMaterialTranslationFixtureDTO,
)
from src.modules.base.database_model import Language
from src.modules.materials.models import Material, MaterialTranslation
from src.modules.materials.models_dto import (
    MaterialResponseDTO,
    MaterialTranslationResponseDTO,
)


async def create_material_factory(
    session_db: AsyncSession,
    new_material: CreateMaterialFixtureDTO = CreateMaterialFixtureDTO(),
) -> MaterialResponseDTO:
    if new_material.material_group_id is None:
        group_dto = await create_material_group_factory(session_db=session_db)
        material_group_id = group_dto.id
    else:
        material_group_id = new_material.material_group_id

    if new_material.index is None:
        stmt = (
            select(func.coalesce(func.max(Material.index), 0))
            .where(Material.material_group_id == material_group_id)
        )
        max_idx = (await session_db.execute(stmt)).scalar_one()
        index = max_idx + 1
    else:
        index = new_material.index

    material = Material(
        material_group_id=material_group_id,
        code=random_string() if new_material.code is None else new_material.code,
        index=index,
        is_active=True if new_material.is_active is None else new_material.is_active,
    )
    session_db.add(material)
    await session_db.flush()

    # Создаем дефолтный перевод (ENG)
    trans = MaterialTranslation(
        material_id=material.id,
        locale=new_material.locale if new_material.locale is not None else Language.ENG,
        name=new_material.name if new_material.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()

    result = await session_db.execute(
        select(Material)
        .options(selectinload(Material.translations))
        .where(Material.id == material.id)
    )
    loaded_material = result.scalar_one()

    return MaterialResponseDTO.model_validate(loaded_material)


async def create_material_translation_factory(
    session_db: AsyncSession,
    new_trans: CreateMaterialTranslationFixtureDTO = CreateMaterialTranslationFixtureDTO(),
) -> MaterialTranslationResponseDTO:
    if new_trans.material_id is None:
        material_dto = await create_material_factory(session_db=session_db)
        material_id = material_dto.id
    else:
        material_id = new_trans.material_id

    trans = MaterialTranslation(
        material_id=material_id,
        locale=new_trans.locale if new_trans.locale is not None else Language.GER,
        name=new_trans.name if new_trans.name is not None else random_string(),
    )
    session_db.add(trans)
    await session_db.commit()
    await session_db.refresh(trans)

    return MaterialTranslationResponseDTO.model_validate(trans)
