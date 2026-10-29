from typing import Callable, Awaitable
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.configurator_setting.fixtures.models_dto import CreateConfiguratorSettingFixtureDTO
from tests.modules.configurator_setting.fixtures.factory import create_configurator_setting_factory
from src.modules.configurator_setting.models_dto import ConfiguratorSettingResponseDTO


@pytest_asyncio.fixture(scope="function")
async def create_configurator_setting_fixture(
    session_db: AsyncSession,
) -> Callable[[CreateConfiguratorSettingFixtureDTO], Awaitable[ConfiguratorSettingResponseDTO]]:
    async def _factory(
        new_setting: CreateConfiguratorSettingFixtureDTO = CreateConfiguratorSettingFixtureDTO(),
    ) -> ConfiguratorSettingResponseDTO:
        return await create_configurator_setting_factory(
            session_db=session_db,
            new_setting=new_setting,
        )

    return _factory
