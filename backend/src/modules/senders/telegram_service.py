import logging
from typing import Union

import httpx

from src.core.config.config import Config
from src.modules.senders.exception import (
    TelegramAPIError,
    TelegramChatNotFoundError,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramNotConfiguredError,
    TelegramRateLimitError,
    TelegramSenderException,
)

logger = logging.getLogger(__name__)


class TelegramSenderService:
    """
    Низкоуровневый сервис отправки сообщений в Telegram через Bot API.
    Не зависит от базы данных и ORM-моделей.
    """

    def __init__(self, config: Config, timeout: float = 10.0):
        self.config = config
        self.timeout = timeout

    def _validate_configuration(self) -> None:
        if not self.config.telegram.is_configured:
            raise TelegramNotConfiguredError("TELEGRAM_BOT_TOKEN is not configured in environment")

    async def send_message(
        self,
        chat_id: Union[str, int],
        text: str,
        parse_mode: str = "HTML",
    ) -> bool:
        """
        Отправляет текстовое сообщение в указанный Telegram-чат.
        """
        self._validate_configuration()

        str_chat_id = str(chat_id).strip()
        if not str_chat_id:
            raise TelegramSenderException("Telegram chat_id cannot be empty")

        url = f"https://api.telegram.org/bot{self.config.telegram.bot_token}/sendMessage"
        payload = {
            "chat_id": str_chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as e:
            err_msg = f"Telegram API timeout after {self.timeout}s while sending to chat '{str_chat_id}'"
            logger.error(err_msg)
            raise TelegramNetworkError(err_msg) from e
        except httpx.ConnectError as e:
            err_msg = f"Telegram API connection failed for chat '{str_chat_id}': unable to reach api.telegram.org"
            logger.error(err_msg)
            raise TelegramNetworkError(err_msg) from e
        except httpx.HTTPError as e:
            err_msg = f"Telegram HTTP network transport error for chat '{str_chat_id}': {e}"
            logger.error(err_msg)
            raise TelegramNetworkError(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error while sending Telegram message to '{str_chat_id}': {e}"
            logger.error(err_msg, exc_info=True)
            raise TelegramSenderException(err_msg) from e

        if response.status_code == 200:
            logger.info("Telegram message successfully sent to chat %s", str_chat_id)
            return True

        # Разбор ошибки Telegram Bot API
        try:
            err_json = response.json()
            err_code = err_json.get("error_code", response.status_code)
            err_desc = err_json.get("description", response.text)
        except Exception:
            err_code = response.status_code
            err_desc = response.text

        err_desc_lower = str(err_desc).lower()
        if err_code == 400 and "chat not found" in err_desc_lower:
            diag = f"Telegram chat '{str_chat_id}' was not found. Check site settings or start the bot."
            logger.error(diag)
            raise TelegramChatNotFoundError(diag)
        elif err_code == 401:
            diag = "Telegram Unauthorized (401): TELEGRAM_BOT_TOKEN is invalid or revoked. Check .env."
            logger.error(diag)
            raise TelegramAPIError(diag)
        elif err_code == 403:
            diag = f"Telegram Forbidden (403): Bot lacks permission to send to '{str_chat_id}' ({err_desc})"
            logger.error(diag)
            raise TelegramForbiddenError(diag)
        elif err_code == 429:
            diag = f"Telegram Too Many Requests (429): Rate limit exceeded ({err_desc})"
            logger.error(diag)
            raise TelegramRateLimitError(diag)
        else:
            diag = f"Telegram API error ({err_code}): {err_desc}"
            logger.error(diag)
            raise TelegramAPIError(diag)
