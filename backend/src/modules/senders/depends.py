from fastapi import Depends

from src.core.config.config import Config
from src.modules.depends import get_config
from src.modules.senders.email_service import EmailSenderService
from src.modules.senders.telegram_service import TelegramSenderService


def get_email_sender_service(
    config: Config = Depends(get_config),
) -> EmailSenderService:
    return EmailSenderService(config=config)


def get_telegram_sender_service(
    config: Config = Depends(get_config),
) -> TelegramSenderService:
    return TelegramSenderService(config=config)
