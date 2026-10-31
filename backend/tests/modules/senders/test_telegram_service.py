from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.core.config.config import Config, TelegramConfig
from src.modules.senders.exception import (
    TelegramAPIError,
    TelegramChatNotFoundError,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramNotConfiguredError,
    TelegramRateLimitError,
    TelegramSenderException,
)
from src.modules.senders.telegram_service import TelegramSenderService


@pytest.fixture
def telegram_config() -> Config:
    config = Config()
    config.telegram = TelegramConfig(
        bot_token="123456:ABC-DEF_TEST_TOKEN",
    )
    return config


@pytest.mark.asyncio
async def test_telegram_send_success(telegram_config):
    service = TelegramSenderService(config=telegram_config)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200, json={"ok": True})

        result = await service.send_message(
            chat_id="-100123456789",
            text="Hello <b>Telegram</b>",
            parse_mode="HTML",
        )

        assert result is True
        assert mock_post.call_count == 1
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["chat_id"] == "-100123456789"
        assert kwargs["json"]["text"] == "Hello <b>Telegram</b>"
        assert kwargs["json"]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_telegram_not_configured_raises_error():
    config = Config()
    config.telegram = TelegramConfig(bot_token="")
    service = TelegramSenderService(config=config)

    with pytest.raises(TelegramNotConfiguredError):
        await service.send_message(chat_id="123", text="Hi")


@pytest.mark.asyncio
async def test_telegram_empty_chat_id_raises_error(telegram_config):
    service = TelegramSenderService(config=telegram_config)

    with pytest.raises(TelegramSenderException):
        await service.send_message(chat_id="   ", text="Hi")


@pytest.mark.asyncio
async def test_telegram_chat_not_found_raises_custom_exception(telegram_config):
    service = TelegramSenderService(config=telegram_config)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(
            400,
            json={"error_code": 400, "description": "Bad Request: chat not found"},
        )

        with pytest.raises(TelegramChatNotFoundError):
            await service.send_message(chat_id="nonexistent_chat", text="Hello")


@pytest.mark.asyncio
async def test_telegram_forbidden_raises_custom_exception(telegram_config):
    service = TelegramSenderService(config=telegram_config)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(
            403,
            json={"error_code": 403, "description": "Forbidden: bot was blocked by the user"},
        )

        with pytest.raises(TelegramForbiddenError):
            await service.send_message(chat_id="blocked_user", text="Hello")


@pytest.mark.asyncio
async def test_telegram_rate_limit_raises_custom_exception(telegram_config):
    service = TelegramSenderService(config=telegram_config)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(
            429,
            json={"error_code": 429, "description": "Too Many Requests: retry after 30"},
        )

        with pytest.raises(TelegramRateLimitError):
            await service.send_message(chat_id="12345", text="Hello")


@pytest.mark.asyncio
async def test_telegram_timeout_raises_network_error(telegram_config):
    service = TelegramSenderService(config=telegram_config)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Read timeout")

        with pytest.raises(TelegramNetworkError):
            await service.send_message(chat_id="12345", text="Hello")
