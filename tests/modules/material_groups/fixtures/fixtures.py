from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.material_groups.fixtures.models_dto import (
    CreateMaterialGroupFixtureDTO,
    CreateMaterialGroupTranslationFixtureDTO,
)
from tests.modules.material_groups.fixtures.factory import (
    create_material_group_factory,
    create_material_group_translation_factory,
)
from src.modules.material_groups.models_dto import (
    MaterialGroupResponseDTO,
    MaterialGroupTranslationResponseDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_material_group_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateMaterialGroupFixtureDTO], Awaitable[MaterialGroupResponseDTO]]:
    async def _factory(
        new_group: CreateMaterialGroupFixtureDTO = CreateMaterialGroupFixtureDTO(),
    ) -> MaterialGroupResponseDTO:
        return await create_material_group_factory(
            session_db=session_db,
            new_group=new_group,
        )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_material_group_translation_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateMaterialGroupTranslationFixtureDTO], Awaitable[MaterialGroupTranslationResponseDTO]]:
    async def _factory(
        new_trans: CreateMaterialGroupTranslationFixtureDTO = CreateMaterialGroupTranslationFixtureDTO(),
    ) -> MaterialGroupTranslationResponseDTO:
        return await create_material_group_translation_factory(
            session_db=session_db,
            new_trans=new_trans,
        )

    return _factory
