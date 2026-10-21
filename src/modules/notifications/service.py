import html
import logging
from email.message import EmailMessage
from typing import Optional, Tuple

import aiosmtplib
import httpx

from src.core.config.config import Config
from src.modules.quote_requests.models_dto import QuoteRequestResponseDTO
from src.modules.settings.models_dto import SettingsResponseDTO
from src.modules.settings.service import SettingsService

logger = logging.getLogger(__name__)


EMAIL_TRANSLATIONS = {
    "ger": {
        "subject": "Auftragsbestätigung {request_number} — {company_name}",
        "greeting": "Hallo {name}!\n",
        "intro": "Vielen Dank für Ihre Anfrage bei {company_name}.",
        "registered": "Ihre Anfrage wurde erfolgreich unter der Nummer {request_number} registriert.",
        "total": "Gesamtbetrag: {total_price:.2f} {currency}",
        "urgent": "⚡ Status: Dringende Bestellung (Express-Fertigung)",
        "ropes_header": "\nBestellübersicht (Seile):",
        "end_a": "Ende A",
        "end_b": "Ende B",
        "services_header": "\nDienstleistungen & Spleiße:",
        "extras_header": "\nZusatzoptionen:",
        "comment_header": "\nIhr Kommentar zur Anfrage:\n{comment}",
        "footer": "\nUnser Kundenservice wird sich in Kürze mit Ihnen in Verbindung setzen.",
        "phone": "Telefon: {phone}",
        "email": "E-Mail: {email}",
    },
    "eng": {
        "subject": "Order Confirmation {request_number} — {company_name}",
        "greeting": "Hello {name}!\n",
        "intro": "Thank you for choosing {company_name}.",
        "registered": "Your request has been successfully registered with number: {request_number}",
        "total": "Total amount: {total_price:.2f} {currency}",
        "urgent": "⚡ Status: Urgent order (Priority production)",
        "ropes_header": "\nOrder items (Ropes):",
        "end_a": "End A",
        "end_b": "End B",
        "services_header": "\nServices & Splices:",
        "extras_header": "\nExtra options:",
        "comment_header": "\nYour comment:\n{comment}",
        "footer": "\nOur specialist will contact you shortly to confirm the details.",
        "phone": "Phone: {phone}",
        "email": "Email: {email}",
    },
    "rus": {
        "subject": "Подтверждение заявки {request_number} — {company_name}",
        "greeting": "Здравствуйте, {name}!\n",
        "intro": "Благодарим вас за обращение в компанию {company_name}.",
        "registered": "Ваша заявка успешно зарегистрирована под номером: {request_number}",
        "total": "Итоговая сумма: {total_price:.2f} {currency}",
        "urgent": "⚡ Статус: Срочный заказ (приоритетное изготовление)",
        "ropes_header": "\nСостав заказа (канаты):",
        "end_a": "Конец A",
        "end_b": "Конец B",
        "services_header": "\nУслуги и заделки:",
        "extras_header": "\nДополнительные опции:",
        "comment_header": "\nВаш комментарий к заявке:\n{comment}",
        "footer": "\nНаш специалист свяжется с вами в ближайшее время.",
        "phone": "Телефон для справок: {phone}",
        "email": "Email поддержки: {email}",
    },
}


class NotificationService:
    def __init__(self, config: Config, settings_service: SettingsService):
        self.config = config
        self.settings_service = settings_service

    @staticmethod
    def _normalize_locale(locale_val: Optional[str]) -> str:
        if not locale_val:
            return "ger"
        normalized = str(locale_val).lower().strip()
        if normalized in ("ru", "rus"):
            return "rus"
        if normalized in ("en", "eng"):
            return "eng"
        return "ger"

    async def notify_new_quote_request(self, quote: QuoteRequestResponseDTO) -> None:
        """
        Фоновая задача для отправки уведомлений по новой заявке:
        - Email клиенту (на языке заказа)
        - Telegram менеджерам (пуш в рабочий чат)
        - Email менеджерам (копия заявки, если настроено)

        Любые ошибки внутри каналов логируются и не прерывают выполнение других каналов.
        """
        try:
            settings = await self.settings_service.get_settings()
        except Exception as e:
            logger.error(
                "Failed to load settings for notification %s: %s",
                quote.request_number,
                e,
                exc_info=True,
            )
            return

        # 1. Отправка Email клиенту
        try:
            await self.send_customer_email(quote, settings)
        except Exception as e:
            logger.error(
                "Failed to send customer email for %s: %s",
                quote.request_number,
                e,
                exc_info=True,
            )

        # 2. Отправка Telegram в чат менеджеров
        try:
            await self.send_manager_telegram(quote, settings)
        except Exception as e:
            logger.error(
                "Failed to send Telegram notification for %s: %s",
                quote.request_number,
                e,
                exc_info=True,
            )

        # 3. Отправка Email копии менеджерам (при включённой опции)
        try:
            await self.send_manager_email(quote, settings)
        except Exception as e:
            logger.error(
                "Failed to send manager email for %s: %s",
                quote.request_number,
                e,
                exc_info=True,
            )

    async def send_customer_email(
        self,
        quote: QuoteRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> bool:
        if not settings.email_notifications_enabled:
            logger.info("Customer email notifications disabled in settings. Skipping for %s", quote.request_number)
            return False

        if not self.config.email.is_configured:
            logger.info("SMTP credentials not configured in env. Skipping customer email for %s", quote.request_number)
            return False

        lang = self._normalize_locale(getattr(quote, "locale", None))
        t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["ger"])

        msg = EmailMessage()
        msg["From"] = self.config.email.from_email
        msg["To"] = quote.email
        msg["Subject"] = t["subject"].format(
            request_number=quote.request_number,
            company_name=settings.company_name,
        )

        currency_val = quote.currency.value if hasattr(quote.currency, "value") else str(quote.currency)
        lines = [
            t["greeting"].format(name=quote.name),
            t["intro"].format(company_name=settings.company_name),
            t["registered"].format(request_number=quote.request_number),
            t["total"].format(total_price=quote.total_price, currency=currency_val),
        ]

        if quote.is_urgent:
            lines.append(t["urgent"])

        if quote.rope_items:
            lines.append(t["ropes_header"])
            for idx, item in enumerate(quote.rope_items, 1):
                item_line = (
                    f"  {idx}. {item.product_name_snapshot} ({item.color_name_snapshot}), "
                    f"{item.diameter_mm} mm, {item.length_m} m"
                )
                if item.end_a_name_snapshot:
                    item_line += f" | {t['end_a']}: {item.end_a_name_snapshot}"
                if item.end_b_name_snapshot:
                    item_line += f" | {t['end_b']}: {item.end_b_name_snapshot}"
                item_line += f" — {item.total_cost:.2f} {currency_val}"
                lines.append(item_line)

        if quote.service_items:
            lines.append(t["services_header"])
            for idx, srv in enumerate(quote.service_items, 1):
                lines.append(
                    f"  {idx}. {srv.service_name_snapshot} ({srv.material_name_snapshot}), "
                    f"{srv.diameter_mm} mm — {srv.total_cost:.2f} {currency_val}"
                )

        if quote.extra_items:
            lines.append(t["extras_header"])
            for idx, extra in enumerate(quote.extra_items, 1):
                lines.append(
                    f"  {idx}. {extra.name_snapshot} x{extra.quantity} — {extra.total_cost:.2f} {currency_val}"
                )

        if quote.comment:
            lines.append(t["comment_header"].format(comment=quote.comment))

        lines.append(t["footer"])
        if settings.contact_phone:
            lines.append(t["phone"].format(phone=settings.contact_phone))
        if settings.contact_email:
            lines.append(t["email"].format(email=settings.contact_email))

        msg.set_content("\n".join(lines))

        await aiosmtplib.send(
            msg,
            hostname=self.config.email.smtp_host,
            port=self.config.email.smtp_port,
            username=self.config.email.smtp_user,
            password=self.config.email.smtp_password,
            start_tls=self.config.email.use_tls,
        )
        logger.info(
            "Confirmation email (%s) sent to %s for %s",
            lang,
            quote.email,
            quote.request_number,
        )
        return True

    async def send_manager_telegram(
        self,
        quote: QuoteRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> Tuple[bool, Optional[str]]:
        """
        Отправляет уведомление в Telegram менеджерам с детальной обработкой ошибок.
        Возвращает (success: bool, error_message: Optional[str]).
        """
        if not settings.telegram_notifications_enabled:
            logger.info("Telegram notifications disabled in settings. Skipping for %s", quote.request_number)
            return False, "Telegram notifications are disabled in site settings"

        chat_id = settings.telegram_chat_id
        if not chat_id:
            msg = (
                f"Telegram notification skipped for {quote.request_number}: "
                "'telegram_chat_id' is not configured in site settings."
            )
            logger.warning(msg)
            return False, msg

        if not self.config.telegram.is_configured:
            msg = (
                f"Telegram notification skipped for {quote.request_number}: "
                "'TELEGRAM_BOT_TOKEN' is not configured in environment variables."
            )
            logger.warning(msg)
            return False, msg

        urgent_badge = "🚨 <b>ВНИМАНИЕ: СРОЧНЫЙ ЗАКАЗ!</b>\n" if quote.is_urgent else ""
        escaped_name = html.escape(quote.name)
        escaped_email = html.escape(quote.email)
        escaped_phone = html.escape(quote.phone or "не указан")
        escaped_comment = html.escape(quote.comment or "—")
        currency_val = quote.currency.value if hasattr(quote.currency, "value") else str(quote.currency)

        text = (
            f"{urgent_badge}"
            f"🆕 <b>Новая заявка:</b> <code>{html.escape(quote.request_number)}</code>\n"
            f"👤 <b>Клиент:</b> {escaped_name}\n"
            f"📧 <b>Email:</b> {escaped_email}\n"
            f"📞 <b>Телефон:</b> {escaped_phone}\n"
            f"💰 <b>Сумма:</b> <b>{quote.total_price:.2f} {currency_val}</b>\n"
            f"💬 <b>Комментарий:</b> {escaped_comment}\n"
        )

        if quote.rope_items:
            text += f"🪢 <b>Позиций канатов:</b> {len(quote.rope_items)}\n"

        url = f"https://api.telegram.org/bot{self.config.telegram.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
        except httpx.TimeoutException as e:
            err = (
                f"Telegram API timeout after 10.0s while sending notification for {quote.request_number} "
                f"to chat '{chat_id}'. Check network connectivity."
            )
            logger.error(err)
            return False, err
        except httpx.ConnectError as e:
            err = (
                f"Telegram API connection failed for {quote.request_number} to chat '{chat_id}': "
                f"Unable to reach api.telegram.org ({e}). Check DNS/firewall/proxy."
            )
            logger.error(err)
            return False, err
        except httpx.HTTPError as e:
            err = f"Telegram HTTP network transport error for {quote.request_number} to chat '{chat_id}': {e}"
            logger.error(err)
            return False, err
        except Exception as e:
            err = f"Unexpected error while sending Telegram notification for {quote.request_number}: {e}"
            logger.error(err, exc_info=True)
            return False, err

        # Обработка ответов API Telegram
        if response.status_code == 200:
            logger.info("Telegram notification sent for %s to chat %s", quote.request_number, chat_id)
            return True, None

        # Разбор ошибки от Telegram Bot API
        try:
            err_json = response.json()
            err_code = err_json.get("error_code", response.status_code)
            err_desc = err_json.get("description", response.text)
        except Exception:
            err_code = response.status_code
            err_desc = response.text

        # Человекочитаемая диагностика
        if err_code == 400:
            if "chat not found" in err_desc.lower():
                diagnostic = (
                    f"Telegram chat '{chat_id}' was not found. Verify the chat ID in site settings, "
                    "or ensure the bot has been added to the chat/channel and user started the bot."
                )
            elif "can't parse entities" in err_desc.lower():
                diagnostic = f"Telegram HTML markup parsing error in notification text: {err_desc}"
            else:
                diagnostic = f"Telegram Bad Request (400): {err_desc}"
        elif err_code == 401:
            diagnostic = "Telegram Unauthorized (401): TELEGRAM_BOT_TOKEN is invalid or revoked. Check .env."
        elif err_code == 403:
            diagnostic = (
                f"Telegram Forbidden (403): Bot lacks permission to send messages to chat '{chat_id}'. "
                f"The bot may be blocked by user, kicked from group, or not an administrator in the channel. ({err_desc})"
            )
        elif err_code == 429:
            diagnostic = f"Telegram Too Many Requests (429): Rate limit exceeded. Details: {err_desc}"
        elif 500 <= err_code < 600:
            diagnostic = f"Telegram Server Error ({err_code}): api.telegram.org internal error. Details: {err_desc}"
        else:
            diagnostic = f"Telegram API error ({err_code}): {err_desc}"

        logger.error(
            "Failed to send Telegram notification for %s (Status: %d): %s",
            quote.request_number,
            err_code,
            diagnostic,
        )
        return False, diagnostic

    async def send_manager_email(
        self,
        quote: QuoteRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> bool:
        if not settings.manager_email_notifications_enabled or not settings.manager_notification_email:
            return False

        if not self.config.email.is_configured:
            return False

        currency_val = quote.currency.value if hasattr(quote.currency, "value") else str(quote.currency)
        msg = EmailMessage()
        msg["From"] = self.config.email.from_email
        msg["To"] = settings.manager_notification_email
        urgent_prefix = "[СРОЧНО] " if quote.is_urgent else ""
        msg["Subject"] = (
            f"{urgent_prefix}Новая заявка {quote.request_number} на сумму "
            f"{quote.total_price:.2f} {currency_val}"
        )

        body = (
            f"Поступила новая заявка {quote.request_number}\n\n"
            f"Клиент: {quote.name}\n"
            f"Email: {quote.email}\n"
            f"Телефон: {quote.phone or 'не указан'}\n"
            f"Сумма: {quote.total_price:.2f} {currency_val}\n"
            f"Комментарий: {quote.comment or 'нет'}\n"
        )
        msg.set_content(body)

        await aiosmtplib.send(
            msg,
            hostname=self.config.email.smtp_host,
            port=self.config.email.smtp_port,
            username=self.config.email.smtp_user,
            password=self.config.email.smtp_password,
            start_tls=self.config.email.use_tls,
        )
        logger.info("Manager copy email sent to %s for %s", settings.manager_notification_email, quote.request_number)
        return True
