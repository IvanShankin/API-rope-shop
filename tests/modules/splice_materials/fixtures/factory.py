from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.functions import random_string
from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from src.modules.splice_materials.models import SpliceMaterial
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO


async def create_splice_material_factory(
    session_db: AsyncSession,
    new_material: CreateSpliceMaterialFixtureDTO = CreateSpliceMaterialFixtureDTO(),
) -> SpliceMaterialResponseDTO:
    material = SpliceMaterial(
        code=random_string() if new_material.code is None else new_material.code,
        name=random_string() if new_material.name is None else new_material.name,
    )
    session_db.add(material)
    await session_db.commit()
    await session_db.refresh(material)

    return SpliceMaterialResponseDTO.model_validate(material)
