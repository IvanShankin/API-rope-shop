from fastapi import Depends, Request

from src.modules.notifications.service import NotificationService
from src.modules.settings.depends import get_settings_service
from src.modules.settings.service import SettingsService


def get_notification_service(
    request: Request,
    settings_service: SettingsService = Depends(get_settings_service),
) -> NotificationService:
    return NotificationService(
        config=request.app.state.config,
        settings_service=settings_service,
    )
