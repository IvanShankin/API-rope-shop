from typing import Tuple

import pytest_asyncio

from tests.modules.splice_materials.fixtures.models_dto import CreateSpliceMaterialFixtureDTO
from src.modules.splice_materials.models_dto import SpliceMaterialResponseDTO
from tests.modules.splice_materials.fixtures.factory import create_splice_material_factory


@pytest_asyncio.fixture(scope="function")
async def create_splice_material_fixture(
    not_open_session_db
):
    """
    :return: Возвращает функцию -> функция возвращает `SpliceMaterialResponseDTO`
    """

    async def _factory(
        new_material: CreateSpliceMaterialFixtureDTO = CreateSpliceMaterialFixtureDTO(),
    ) -> SpliceMaterialResponseDTO:
        async with not_open_session_db() as session:
            material = await create_splice_material_factory(
                session_db=session,
                new_material=new_material,
            )
            return material

    return _factory
