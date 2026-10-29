from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.configurator_setting.repository import ConfiguratorSettingRepository
from src.modules.configurator_setting.service import ConfiguratorSettingService


def get_configurator_setting_repository(
    session: AsyncSession = Depends(get_db),
) -> ConfiguratorSettingRepository:
    return ConfiguratorSettingRepository(session=session)


def get_configurator_setting_service(
    repo: ConfiguratorSettingRepository = Depends(get_configurator_setting_repository),
    session: AsyncSession = Depends(get_db),
) -> ConfiguratorSettingService:
    return ConfiguratorSettingService(repo=repo, session=session)
