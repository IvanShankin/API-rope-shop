from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.configurators.repository import ConfiguratorRepository
from src.modules.configurators.service import ConfiguratorService


def get_configurator_repository(session: AsyncSession = Depends(get_db)) -> ConfiguratorRepository:
    return ConfiguratorRepository(session=session)


def get_configurators_service(
    repo: ConfiguratorRepository = Depends(get_configurator_repository),
    session: AsyncSession = Depends(get_db),
) -> ConfiguratorService:
    return ConfiguratorService(repo=repo, session=session)
