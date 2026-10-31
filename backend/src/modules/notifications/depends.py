from fastapi import Depends, Request

from src.modules.notifications.service import NotificationService
from src.modules.senders.depends import (
    get_email_sender_service,
    get_telegram_sender_service,
)
from src.modules.senders.email_service import EmailSenderService
from src.modules.senders.telegram_service import TelegramSenderService
from src.modules.settings.depends import get_settings_service
from src.modules.settings.service import SettingsService


def get_notification_service(
    request: Request,
    settings_service: SettingsService = Depends(get_settings_service),
    email_sender: EmailSenderService = Depends(get_email_sender_service),
    telegram_sender: TelegramSenderService = Depends(get_telegram_sender_service),
) -> NotificationService:
    config = request.app.state.config
    return NotificationService(
        config=config,
        settings_service=settings_service,
        email_sender=email_sender,
        telegram_sender=telegram_sender,
    )
