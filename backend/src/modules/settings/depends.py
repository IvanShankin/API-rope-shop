from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.core.database.database import get_db
from src.modules.depends import get_config
from src.modules.settings.repository import SettingsRepository
from src.modules.settings.service import SettingsService


def get_settings_service(
    session: AsyncSession = Depends(get_db),
    config: Config = Depends(get_config),
) -> SettingsService:
    return SettingsService(
        repo=SettingsRepository(session=session),
        session=session,
        config=config,
    )
