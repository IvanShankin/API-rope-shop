from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import get_db
from src.modules.configurator_extra.repository import (
    ConfiguratorExtraRepository,
    ConfiguratorExtraTranslationRepository,
)
from src.modules.configurator_extra.service import ConfiguratorExtraService


def get_configurator_extra_repository(
    session: AsyncSession = Depends(get_db),
) -> ConfiguratorExtraRepository:
    return ConfiguratorExtraRepository(session=session)


def get_configurator_extra_translation_repository(
    session: AsyncSession = Depends(get_db),
) -> ConfiguratorExtraTranslationRepository:
    return ConfiguratorExtraTranslationRepository(session=session)


def get_configurator_extra_service(
    extra_repo: ConfiguratorExtraRepository = Depends(get_configurator_extra_repository),
    translation_repo: ConfiguratorExtraTranslationRepository = Depends(get_configurator_extra_translation_repository),
    session: AsyncSession = Depends(get_db),
) -> ConfiguratorExtraService:
    return ConfiguratorExtraService(
        extra_repo=extra_repo,
        translation_repo=translation_repo,
        session=session,
    )
