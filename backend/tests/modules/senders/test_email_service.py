from unittest.mock import AsyncMock, patch

import aiosmtplib
import pytest

from src.core.config.config import Config, EmailConfig
from src.modules.senders.email_service import EmailSenderService
from src.modules.senders.exception import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailNotConfiguredError,
    EmailRecipientError,
    EmailSenderException,
)


@pytest.fixture
def email_config() -> Config:
    config = Config()
    config.email = EmailConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="test@example.com",
        smtp_password="secret_password",
        from_email="noreply@ropeshop.com",
        use_tls=True,
    )
    return config


@pytest.mark.asyncio
async def test_send_email_success(email_config):
    service = EmailSenderService(config=email_config)

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        result = await service.send_email(
            to_email="client@example.com",
            subject="Test Subject",
            body="Hello, this is a test.",
        )

        assert result is True
        assert mock_send.call_count == 1
        sent_msg = mock_send.call_args[0][0]
        assert sent_msg["To"] == "client@example.com"
        assert sent_msg["From"] == "noreply@ropeshop.com"
        assert sent_msg["Subject"] == "Test Subject"


@pytest.mark.asyncio
async def test_send_email_with_html_success(email_config):
    service = EmailSenderService(config=email_config)

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        result = await service.send_email(
            to_email="client@example.com",
            subject="HTML Subject",
            body="Text body",
            html_body="<h1>HTML body</h1>",
            from_email="custom@ropeshop.com",
        )

        assert result is True
        sent_msg = mock_send.call_args[0][0]
        assert sent_msg["From"] == "custom@ropeshop.com"


@pytest.mark.asyncio
async def test_send_email_empty_recipient_raises_error(email_config):
    service = EmailSenderService(config=email_config)

    with pytest.raises(EmailRecipientError):
        await service.send_email(
            to_email="",
            subject="Subject",
            body="Body",
        )


@pytest.mark.asyncio
async def test_send_email_not_configured_raises_error():
    config = Config()
    config.email = EmailConfig(
        smtp_host="",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        from_email="",
    )
    service = EmailSenderService(config=config)

    with pytest.raises(EmailNotConfiguredError):
        await service.send_email(
            to_email="test@example.com",
            subject="Subject",
            body="Body",
        )


@pytest.mark.asyncio
async def test_send_email_auth_error_raises_custom_exception(email_config):
    service = EmailSenderService(config=email_config)

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = aiosmtplib.SMTPAuthenticationError(535, "Auth failed")

        with pytest.raises(EmailAuthenticationError):
            await service.send_email(
                to_email="client@example.com",
                subject="Subject",
                body="Body",
            )


@pytest.mark.asyncio
async def test_send_email_connect_error_raises_custom_exception(email_config):
    service = EmailSenderService(config=email_config)

    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = aiosmtplib.SMTPConnectError("Connection refused")

        with pytest.raises(EmailConnectionError):
            await service.send_email(
                to_email="client@example.com",
                subject="Subject",
                body="Body",
            )
