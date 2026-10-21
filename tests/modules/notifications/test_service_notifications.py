from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.core.config.config import Config, EmailConfig, TelegramConfig
from src.modules.configurator_setting.models import Currency
from src.modules.notifications.service import NotificationService
from src.modules.quote_requests.models import ConfiguratorType, QuoteRequestStatus
from src.modules.quote_requests.models_dto import (
    QuoteRequestResponseDTO,
    QuoteRopeItemResponseDTO,
)
from src.modules.settings.models_dto import SettingsResponseDTO


def _create_sample_quote_dto(locale: str = "ger") -> QuoteRequestResponseDTO:
    return QuoteRequestResponseDTO(
        id=1,
        request_number="RPL-2026-0001-01",
        configurator_type=ConfiguratorType.ROPE_WITH_SPLICE,
        name="Max Mustermann",
        email="max@example.com",
        phone="+49 170 1234567",
        comment="Please deliver by Friday.",
        currency=Currency.EUR,
        subtotal=120.0,
        urgent_surcharge=20.0,
        total_price=140.0,
        vat_rate=19.0,
        is_urgent=True,
        status=QuoteRequestStatus.NEW,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        locale=locale,
        rope_items=[
            QuoteRopeItemResponseDTO(
                id=1,
                quote_request_id=1,
                product_id=10,
                color_id=5,
                product_name_snapshot="Classic Static Rope",
                color_name_snapshot="Red",
                diameter_mm=10.5,
                length_m=50.0,
                quantity=1,
                price_per_meter_snapshot=2.0,
                total_rope_cost=100.0,
                end_a_name_snapshot="Soft Eye Splice",
                end_a_cost=20.0,
                end_b_cost=0.0,
                total_cost=120.0,
            )
        ],
        service_items=[],
        extra_items=[],
    )


def _create_mock_settings_service(settings: SettingsResponseDTO) -> MagicMock:
    service = MagicMock()
    service.get_settings = AsyncMock(return_value=settings)
    return service


@pytest.mark.asyncio
async def test_notify_new_quote_request_german_email_and_telegram():
    config = Config()
    config.email = EmailConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="test_password",
        from_email="noreply@ropeshop.com",
    )
    config.telegram = TelegramConfig(
        bot_token="123456:ABC-DEF",
    )

    settings = SettingsResponseDTO(
        id=1,
        telegram_chat_id="-100987654321",
        telegram_notifications_enabled=True,
        email_notifications_enabled=True,
        manager_notification_email=None,
        manager_email_notifications_enabled=False,
        company_name="Alpine Rope Shop",
        contact_email="support@ropeshop.com",
        contact_phone="+49 111 222",
        site_url="https://ropeshop.com",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    quote = _create_sample_quote_dto(locale="ger")
    mock_settings_service = _create_mock_settings_service(settings)
    service = NotificationService(config=config, settings_service=mock_settings_service)

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_post.return_value.status_code = 200

        await service.notify_new_quote_request(quote=quote)

        # Проверяем немецкое письмо
        assert mock_send.call_count == 1
        sent_msg = mock_send.call_args[0][0]
        assert sent_msg["To"] == "max@example.com"
        assert "Auftragsbestätigung" in sent_msg["Subject"]
        msg_content = sent_msg.get_content()
        assert "Hallo Max Mustermann!" in msg_content
        assert "Bestellübersicht (Seile):" in msg_content
        assert "140.00 EUR" in msg_content

        # Проверяем Telegram
        assert mock_post.call_count == 1
        telegram_url = mock_post.call_args[0][0]
        assert "123456:ABC-DEF/sendMessage" in telegram_url
        telegram_json = mock_post.call_args[1]["json"]
        assert telegram_json["chat_id"] == "-100987654321"
        assert "RPL-2026-0001-01" in telegram_json["text"]


@pytest.mark.asyncio
async def test_notify_new_quote_request_english_and_russian_email():
    config = Config()
    config.email = EmailConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="test_password",
        from_email="noreply@ropeshop.com",
    )
    config.telegram = TelegramConfig()

    settings = SettingsResponseDTO(
        id=1,
        telegram_notifications_enabled=False,
        email_notifications_enabled=True,
        company_name="Rope Shop",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    mock_settings_service = _create_mock_settings_service(settings)
    service = NotificationService(config=config, settings_service=mock_settings_service)

    # 1. English
    quote_en = _create_sample_quote_dto(locale="en")
    quote_en.name = "John Doe"
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await service.send_customer_email(quote=quote_en, settings=settings)
        msg_en = mock_send.call_args[0][0]
        assert "Order Confirmation" in msg_en["Subject"]
        assert "Hello John Doe!" in msg_en.get_content()
        assert "Thank you for choosing" in msg_en.get_content()

    # 2. Russian
    quote_ru = _create_sample_quote_dto(locale="ru")
    quote_ru.name = "Иван Иванов"
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await service.send_customer_email(quote=quote_ru, settings=settings)
        msg_ru = mock_send.call_args[0][0]
        assert "Подтверждение заявки" in msg_ru["Subject"]
        assert "Здравствуйте, Иван Иванов!" in msg_ru.get_content()
        assert "Благодарим вас за обращение" in msg_ru.get_content()


@pytest.mark.asyncio
async def test_telegram_error_handling_chat_not_found():
    config = Config()
    config.telegram = TelegramConfig(bot_token="123456:ABC-DEF")
    settings = SettingsResponseDTO(
        id=1,
        telegram_chat_id="-99999999",
        telegram_notifications_enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    quote = _create_sample_quote_dto()
    service = NotificationService(config=config, settings_service=MagicMock())

    # Мокаем 400 Bad Request: chat not found
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "ok": False,
        "error_code": 400,
        "description": "Bad Request: chat not found",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success, err = await service.send_manager_telegram(quote=quote, settings=settings)

        assert success is False
        assert "was not found" in err


@pytest.mark.asyncio
async def test_telegram_error_handling_unauthorized():
    config = Config()
    config.telegram = TelegramConfig(bot_token="invalid_token")
    settings = SettingsResponseDTO(
        id=1,
        telegram_chat_id="-100123",
        telegram_notifications_enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    quote = _create_sample_quote_dto()
    service = NotificationService(config=config, settings_service=MagicMock())

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"ok": False, "error_code": 401, "description": "Unauthorized"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success, err = await service.send_manager_telegram(quote=quote, settings=settings)

        assert success is False
        assert "TELEGRAM_BOT_TOKEN is invalid" in err


@pytest.mark.asyncio
async def test_telegram_error_handling_timeout():
    config = Config()
    config.telegram = TelegramConfig(bot_token="123:ABC")
    settings = SettingsResponseDTO(
        id=1,
        telegram_chat_id="-100123",
        telegram_notifications_enabled=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    quote = _create_sample_quote_dto()
    service = NotificationService(config=config, settings_service=MagicMock())

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
        success, err = await service.send_manager_telegram(quote=quote, settings=settings)

        assert success is False
        assert "timeout" in err.lower()


@pytest.mark.asyncio
async def test_notifications_disabled_in_settings_skips_sending():
    config = Config()
    config.email = EmailConfig(
        smtp_host="smtp.test.com",
        smtp_port=587,
        smtp_user="test@test.com",
        smtp_password="test_password",
        from_email="noreply@ropeshop.com",
    )
    config.telegram = TelegramConfig(bot_token="123456:ABC-DEF")

    settings = SettingsResponseDTO(
        id=1,
        telegram_chat_id="-100987654321",
        telegram_notifications_enabled=False,
        email_notifications_enabled=False,
        company_name="Alpine Rope Shop",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    quote = _create_sample_quote_dto()
    mock_settings_service = _create_mock_settings_service(settings)
    service = NotificationService(config=config, settings_service=mock_settings_service)

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        await service.notify_new_quote_request(quote=quote)

        assert mock_send.call_count == 0
        assert mock_post.call_count == 0
