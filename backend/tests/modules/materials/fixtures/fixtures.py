from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.materials.fixtures.models_dto import (
    CreateMaterialFixtureDTO,
    CreateMaterialTranslationFixtureDTO,
)
from tests.modules.materials.fixtures.factory import (
    create_material_factory,
    create_material_translation_factory,
)
from src.modules.materials.models_dto import (
    MaterialResponseDTO,
    MaterialTranslationResponseDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_material_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateMaterialFixtureDTO], Awaitable[MaterialResponseDTO]]:
    async def _factory(
        new_material: CreateMaterialFixtureDTO = CreateMaterialFixtureDTO(),
    ) -> MaterialResponseDTO:
        return await create_material_factory(
            session_db=session_db,
            new_material=new_material,
        )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_material_translation_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateMaterialTranslationFixtureDTO], Awaitable[MaterialTranslationResponseDTO]]:
    async def _factory(
        new_trans: CreateMaterialTranslationFixtureDTO = CreateMaterialTranslationFixtureDTO(),
    ) -> MaterialTranslationResponseDTO:
        return await create_material_translation_factory(
            session_db=session_db,
            new_trans=new_trans,
        )

    return _factory
