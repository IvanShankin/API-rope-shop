import logging
from email.message import EmailMessage
from typing import Optional

import aiosmtplib

from src.core.config.config import Config
from src.modules.senders.exception import (
    EmailAuthenticationError,
    EmailConnectionError,
    EmailNotConfiguredError,
    EmailRecipientError,
    EmailSenderException,
)

logger = logging.getLogger(__name__)


class EmailSenderService:
    """
    Низкоуровневый сервис отправки email-сообщений через SMTP.
    Не зависит от базы данных и ORM-моделей.
    """

    def __init__(self, config: Config):
        self.config = config

    def _validate_configuration(self) -> None:
        if not self.config.email.is_configured:
            raise EmailNotConfiguredError("SMTP credentials are not configured in environment")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """
        Отправляет текстовое (и опционально HTML) email-сообщение.
        """
        if not to_email or not to_email.strip():
            raise EmailRecipientError("Recipient email address is required")

        self._validate_configuration()

        msg = EmailMessage()
        sender = from_email or self.config.email.from_email
        msg["From"] = sender
        msg["To"] = to_email.strip()
        msg["Subject"] = subject
        msg.set_content(body)

        if html_body:
            msg.add_alternative(html_body, subtype="html")

        return await self.send_message(msg)

    async def send_message(self, message: EmailMessage) -> bool:
        """
        Отправляет готовый объект EmailMessage через сконфигурированный SMTP сервер.
        """
        self._validate_configuration()

        try:
            await aiosmtplib.send(
                message,
                hostname=self.config.email.smtp_host,
                port=self.config.email.smtp_port,
                username=self.config.email.smtp_user,
                password=self.config.email.smtp_password,
                start_tls=self.config.email.use_tls,
            )
            logger.info("Email sent successfully to %s", message.get("To"))
            return True
        except aiosmtplib.SMTPAuthenticationError as e:
            err_msg = f"SMTP authentication failed: {getattr(e, 'message', str(e))}"
            logger.error(err_msg)
            raise EmailAuthenticationError(err_msg) from e
        except (aiosmtplib.SMTPConnectError, aiosmtplib.SMTPServerDisconnected, TimeoutError, OSError) as e:
            err_msg = f"SMTP connection error: {e}"
            logger.error(err_msg)
            raise EmailConnectionError(err_msg) from e
        except aiosmtplib.SMTPException as e:
            err_msg = f"SMTP protocol error: {getattr(e, 'message', str(e))}"
            logger.error(err_msg)
            raise EmailSenderException(err_msg) from e
        except Exception as e:
            err_msg = f"Unexpected error while sending email: {e}"
            logger.error(err_msg, exc_info=True)
            raise EmailSenderException(err_msg) from e
