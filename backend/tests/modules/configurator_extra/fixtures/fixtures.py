from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.configurator_extra.fixtures.models_dto import (
    CreateConfiguratorExtraFixtureDTO,
    CreateConfiguratorExtraTranslationFixtureDTO,
)
from tests.modules.configurator_extra.fixtures.factory import (
    create_configurator_extra_factory,
    create_configurator_extra_translation_factory,
)
from src.modules.configurator_extra.models_dto import (
    ConfiguratorExtraResponseDTO,
    ConfiguratorExtraTranslationResponseDTO,
)


@pytest_asyncio.fixture(scope="function")
async def create_configurator_extra_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateConfiguratorExtraFixtureDTO], Awaitable[ConfiguratorExtraResponseDTO]]:
    async def _factory(
        new_extra: CreateConfiguratorExtraFixtureDTO = CreateConfiguratorExtraFixtureDTO(),
    ) -> ConfiguratorExtraResponseDTO:
        return await create_configurator_extra_factory(
            session_db=session_db,
            new_extra=new_extra,
        )

    return _factory


@pytest_asyncio.fixture(scope="function")
async def create_configurator_extra_translation_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateConfiguratorExtraTranslationFixtureDTO], Awaitable[ConfiguratorExtraTranslationResponseDTO]]:
    async def _factory(
        new_trans: CreateConfiguratorExtraTranslationFixtureDTO = CreateConfiguratorExtraTranslationFixtureDTO(),
    ) -> ConfiguratorExtraTranslationResponseDTO:
        return await create_configurator_extra_translation_factory(
            session_db=session_db,
            new_trans=new_trans,
        )

    return _factory
