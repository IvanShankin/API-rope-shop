from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.modules.notifications.service import NotificationService
from src.modules.settings.depends import get_settings_service
from src.modules.settings.service import SettingsService


def get_notification_service(
    request: Request,
    settings_service: SettingsService = Depends(get_settings_service),
) -> NotificationService:
    config = request.app.state.config
    session_factory: async_sessionmaker[AsyncSession] | None = getattr(
        config.db_connection, "session_local", None
    )
    return NotificationService(
        config=config,
        settings_service=settings_service,
        session_factory=session_factory,
    )
