from __future__ import annotations

import html
import logging
from typing import TYPE_CHECKING, Optional, Tuple

from src.core.config.config import Config
from src.modules.senders.email_service import EmailSenderService
from src.modules.senders.exception import (
    EmailSenderException,
    TelegramSenderException,
)
from src.modules.senders.telegram_service import TelegramSenderService
from src.modules.settings.models_dto import SettingsResponseDTO
from src.modules.settings.service import SettingsService

if TYPE_CHECKING:
    from src.modules.contact_requests.models_dto import ContactRequestResponseDTO
    from src.modules.quote_requests.models_dto import QuoteRequestResponseDTO

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
        "tracking_link": "\nDen aktuellen Status Ihrer Bestellung können Sie hier einsehen:\n{tracking_url}\n",
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
        "tracking_link": "\nYou can track the status of your order online here:\n{tracking_url}\n",
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
        "tracking_link": "\nОтследить актуальный статус вашего заказа онлайн вы можете по ссылке:\n{tracking_url}\n",
        "footer": "\nНаш специалист свяжется с вами в ближайшее время.",
        "phone": "Телефон для справок: {phone}",
        "email": "Email поддержки: {email}",
    },
}

CONTACT_EMAIL_TRANSLATIONS = {
    "ger": {
        "subject": "Ihre Kontaktanfrage #{contact_id} — {company_name}",
        "greeting": "Hallo {name}!\n",
        "intro": "Vielen Dank für Ihre Anfrage bei {company_name}.",
        "registered": "Ihre Nachricht wurde erfolgreich empfangen (Vorgangsnummer: #{contact_id}).",
        "footer": "\nUnser Team wird sich in Kürze mit Ihnen in Verbindung setzen.",
        "phone": "Telefon: {phone}",
        "email": "E-Mail: {email}",
    },
    "eng": {
        "subject": "Your inquiry #{contact_id} — {company_name}",
        "greeting": "Hello {name}!\n",
        "intro": "Thank you for contacting {company_name}.",
        "registered": "Your message has been successfully received (Inquiry ID: #{contact_id}).",
        "footer": "\nOur team will get back to you shortly.",
        "phone": "Phone: {phone}",
        "email": "Email: {email}",
    },
    "rus": {
        "subject": "Ваше обращение #{contact_id} — {company_name}",
        "greeting": "Здравствуйте, {name}!\n",
        "intro": "Благодарим вас за обращение в компанию {company_name}.",
        "registered": "Ваше сообщение успешно получено (номер обращения: #{contact_id}).",
        "footer": "\nНаш специалист свяжется с вами в ближайшее время.",
        "phone": "Телефон для справок: {phone}",
        "email": "Email поддержки: {email}",
    },
}


class NotificationService:
    def __init__(
        self,
        config: Config,
        settings_service: SettingsService,
        email_sender: EmailSenderService,
        telegram_sender: TelegramSenderService,
    ):
        self.config = config
        self.settings_service = settings_service
        self.email_sender = email_sender
        self.telegram_sender = telegram_sender

    async def get_settings(self) -> SettingsResponseDTO:
        if self.settings_service is None:
            raise RuntimeError("SettingsService is not configured in NotificationService")
        return await self.settings_service.get_settings()

    def can_send_customer_email(
        self,
        settings: SettingsResponseDTO,
        recipient_email: Optional[str] = None,
        identifier: str = "",
    ) -> bool:
        """
        Проверяет возможность и необходимость отправки email клиенту:
        - включены ли email-уведомления в настройках сайта;
        - настроены ли SMTP-параметры сервера;
        - передан ли непустой адрес получателя.
        """
        if not settings.email_notifications_enabled:
            logger.info("Customer email notifications disabled in settings. Skipping for %s", identifier)
            return False

        if not self.config.email.is_configured:
            logger.info("SMTP credentials not configured in env. Skipping customer email for %s", identifier)
            return False

        if not recipient_email or not recipient_email.strip():
            logger.info("Recipient email is empty. Skipping customer email for %s", identifier)
            return False

        return True

    def can_send_manager_email(
        self,
        settings: SettingsResponseDTO,
        manager_email: Optional[str] = None,
        identifier: str = "",
    ) -> bool:
        """
        Проверяет возможность и необходимость отправки email менеджеру:
        - настроены ли SMTP-параметры сервера;
        - включены ли email-уведомления менеджеров / общие email-уведомления;
        - задан ли адрес менеджера.
        """
        if not self.config.email.is_configured:
            logger.info("SMTP credentials not configured in env. Skipping manager email for %s", identifier)
            return False

        if not settings.manager_email_notifications_enabled and not settings.email_notifications_enabled:
            logger.info("Manager email notifications disabled in settings. Skipping for %s", identifier)
            return False

        if not manager_email or not manager_email.strip():
            logger.info("Manager notification email not configured. Skipping manager email for %s", identifier)
            return False

        return True

    def can_send_telegram(
        self,
        settings: SettingsResponseDTO,
        identifier: str = "",
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверяет возможность и необходимость отправки Telegram-уведомления:
        - включены ли TG-уведомления в настройках;
        - задан ли рабочий chat_id в настройках;
        - настроен ли TELEGRAM_BOT_TOKEN в окружении.
        """
        if not settings.telegram_notifications_enabled:
            msg = f"Telegram notifications disabled in settings. Skipping for {identifier}"
            logger.info(msg)
            return False, "Telegram notifications are disabled in site settings"

        chat_id = settings.telegram_chat_id
        if not chat_id or not str(chat_id).strip():
            msg = (
                f"Telegram notification skipped for {identifier}: "
                "'telegram_chat_id' is not configured in site settings."
            )
            logger.warning(msg)
            return False, msg

        if not self.config.telegram.is_configured:
            msg = (
                f"Telegram notification skipped for {identifier}: "
                "'TELEGRAM_BOT_TOKEN' is not configured in environment variables."
            )
            logger.warning(msg)
            return False, msg

        return True, None

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

    async def notify_new_quote_request(
        self,
        quote: QuoteRequestResponseDTO,
        settings: Optional[SettingsResponseDTO] = None,
    ) -> None:
        """
        Фоновая задача для отправки уведомлений по новой заявке:
        - Email клиенту (на языке заказа)
        - Telegram менеджерам (пуш в рабочий чат)
        - Email менеджерам (копия заявки, если настроено)

        Любые ошибки внутри каналов логируются и не прерывают выполнение других каналов.
        """
        try:
            if settings is None:
                settings = await self.get_settings()
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
        if not self.can_send_customer_email(
            settings=settings,
            recipient_email=quote.email,
            identifier=quote.request_number,
        ):
            return False

        lang = self._normalize_locale(getattr(quote, "locale", None))
        t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["ger"])

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

        site_url = settings.site_url or "https://ropeshop.com"
        tracking_token = getattr(quote, "tracking_token", None)
        if tracking_token and hasattr(self.config, "order_tracking"):
            tracking_url = self.config.order_tracking.url_template.format(
                site_url=site_url.rstrip("/"),
                request_number=quote.request_number,
                token=tracking_token,
            )
            if "tracking_link" in t:
                lines.append(t["tracking_link"].format(tracking_url=tracking_url))

        lines.append(t["footer"])
        if settings.contact_phone:
            lines.append(t["phone"].format(phone=settings.contact_phone))
        if settings.contact_email:
            lines.append(t["email"].format(email=settings.contact_email))

        subject = t["subject"].format(
            request_number=quote.request_number,
            company_name=settings.company_name,
        )
        body = "\n".join(lines)

        try:
            await self.email_sender.send_email(
                to_email=quote.email,
                subject=subject,
                body=body,
            )
            logger.info("Confirmation email (%s) sent to %s for %s", lang, quote.email, quote.request_number)
            return True
        except EmailSenderException as e:
            logger.error("Failed to send customer email for %s: %s", quote.request_number, e.message)
            return False
        except Exception as e:
            logger.error("Unexpected error sending customer email for %s: %s", quote.request_number, e, exc_info=True)
            return False

    async def send_manager_telegram(
        self,
        quote: QuoteRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> Tuple[bool, Optional[str]]:
        """
        Отправляет уведомление в Telegram менеджерам с детальной обработкой ошибок.
        Возвращает (success: bool, error_message: Optional[str]).
        """
        can_send, reason = self.can_send_telegram(settings=settings, identifier=quote.request_number)
        if not can_send:
            return False, reason

        chat_id = settings.telegram_chat_id
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

        try:
            await self.telegram_sender.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
            )
            logger.info("Telegram notification sent for %s to chat %s", quote.request_number, chat_id)
            return True, None
        except TelegramSenderException as e:
            logger.error("Failed to send Telegram notification for %s: %s", quote.request_number, e.message)
            return False, e.message
        except Exception as e:
            logger.error("Unexpected error while sending Telegram notification for %s: %s", quote.request_number, e, exc_info=True)
            return False, str(e)

    async def send_manager_email(
        self,
        quote: QuoteRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> bool:
        if not settings.manager_email_notifications_enabled:
            return False

        if not self.can_send_manager_email(
            settings=settings,
            manager_email=settings.manager_notification_email,
            identifier=quote.request_number,
        ):
            return False

        currency_val = quote.currency.value if hasattr(quote.currency, "value") else str(quote.currency)
        urgent_prefix = "[СРОЧНО] " if quote.is_urgent else ""
        subject = (
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

        try:
            await self.email_sender.send_email(
                to_email=settings.manager_notification_email,
                subject=subject,
                body=body,
            )
            logger.info("Manager copy email sent to %s for %s", settings.manager_notification_email, quote.request_number)
            return True
        except EmailSenderException as e:
            logger.error("Failed to send manager email for %s: %s", quote.request_number, e.message)
            return False
        except Exception as e:
            logger.error("Unexpected error sending manager email for %s: %s", quote.request_number, e, exc_info=True)
            return False

    async def notify_new_contact_request(
        self,
        contact: ContactRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> None:
        """
        Фоновая/сервисная задача для отправки уведомлений по новой контактной заявке:
        - Telegram менеджерам (пуш в рабочий чат)
        - Email менеджерам (уведомление о новой заявке)
        - Email клиенту (подтверждение получения)

        Любые ошибки логируются и не прерывают выполнение сервиса.
        """
        # 1. Отправка Telegram в чат менеджеров
        try:
            await self.send_contact_telegram(contact, settings)
        except Exception as e:
            logger.error(
                "Failed to send Telegram notification for contact request #%s: %s",
                getattr(contact, "id", None),
                e,
                exc_info=True,
            )

        # 2. Отправка Email менеджерам (уведомление о новой заявке)
        try:
            await self.send_contact_manager_email(contact, settings)
        except Exception as e:
            logger.error(
                "Failed to send manager email for contact request #%s: %s",
                getattr(contact, "id", None),
                e,
                exc_info=True,
            )

        # 3. Отправка Email клиенту (подтверждение)
        try:
            await self.send_contact_customer_email(contact, settings)
        except Exception as e:
            logger.error(
                "Failed to send customer email for contact request #%s: %s",
                getattr(contact, "id", None),
                e,
                exc_info=True,
            )

    async def send_contact_telegram(
        self,
        contact: ContactRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> Tuple[bool, Optional[str]]:
        """
        Отправляет уведомление в Telegram менеджерам о новой заявке из контактной формы.
        """
        can_send, reason = self.can_send_telegram(settings=settings, identifier=f"contact #{contact.id}")
        if not can_send:
            return False, reason

        escaped_name = html.escape(contact.name)
        escaped_email = html.escape(contact.email)
        escaped_phone = html.escape(contact.phone or "не указан")
        escaped_message = html.escape(contact.message or "—")

        text = (
            f"📩 <b>Новая контактная заявка:</b> <code>#{contact.id}</code>\n"
            f"👤 <b>Клиент:</b> {escaped_name}\n"
            f"📧 <b>Email:</b> {escaped_email}\n"
            f"📞 <b>Телефон:</b> {escaped_phone}\n"
            f"💬 <b>Сообщение:</b>\n{escaped_message}\n"
        )

        try:
            await self.telegram_sender.send_message(
                chat_id=settings.telegram_chat_id,
                text=text,
                parse_mode="HTML",
            )
            logger.info("Telegram notification sent for contact #%s to chat %s", contact.id, settings.telegram_chat_id)
            return True, None
        except TelegramSenderException as e:
            logger.error("Failed to send Telegram notification for contact #%s: %s", contact.id, e.message)
            return False, e.message
        except Exception as e:
            logger.error("Unexpected error sending Telegram message for contact #%s: %s", contact.id, e, exc_info=True)
            return False, str(e)

    async def send_contact_manager_email(
        self,
        contact: ContactRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> bool:
        """
        Отправляет уведомление на почту менеджера о новой контактной заявке.
        """
        to_email = settings.manager_notification_email or settings.contact_email
        if not to_email and hasattr(self.config, "admin"):
            to_email = getattr(self.config.admin, "email", None)

        if not self.can_send_manager_email(
            settings=settings,
            manager_email=to_email,
            identifier=f"contact #{contact.id}",
        ):
            return False

        subject = f"Новая контактная заявка #{contact.id} — {contact.name}"
        body = (
            f"Поступила новая заявка через форму обратной связи #{contact.id}\n\n"
            f"Клиент: {contact.name}\n"
            f"Email: {contact.email}\n"
            f"Телефон: {contact.phone or 'не указан'}\n\n"
            f"Сообщение:\n{contact.message or '—'}\n"
        )

        try:
            await self.email_sender.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
            )
            logger.info("Manager contact email sent to %s for contact #%s", to_email, contact.id)
            return True
        except EmailSenderException as e:
            logger.error("Failed to send manager contact email for #%s: %s", contact.id, e.message)
            return False
        except Exception as e:
            logger.error("Unexpected error sending manager contact email for #%s: %s", contact.id, e, exc_info=True)
            return False

    async def send_contact_customer_email(
        self,
        contact: ContactRequestResponseDTO,
        settings: SettingsResponseDTO,
    ) -> bool:
        """
        Отправляет клиенту подтверждение получения его контактного обращения.
        """
        if not self.can_send_customer_email(
            settings=settings,
            recipient_email=contact.email,
            identifier=f"contact #{contact.id}",
        ):
            return False

        lang = "rus"
        t = CONTACT_EMAIL_TRANSLATIONS.get(lang, CONTACT_EMAIL_TRANSLATIONS["rus"])
        company_name = settings.company_name or "Rope Shop"

        subject = t["subject"].format(contact_id=contact.id, company_name=company_name)
        lines = [
            t["greeting"].format(name=contact.name),
            t["intro"].format(company_name=company_name),
            t["registered"].format(contact_id=contact.id),
            t["footer"],
        ]
        if contact.message:
            lines.append(f"\nВаше сообщение:\n{contact.message}")
        if settings.contact_phone:
            lines.append(t["phone"].format(phone=settings.contact_phone))
        if settings.contact_email:
            lines.append(t["email"].format(email=settings.contact_email))

        body = "\n".join(lines)

        try:
            await self.email_sender.send_email(
                to_email=contact.email,
                subject=subject,
                body=body,
            )
            logger.info("Customer confirmation email sent to %s for contact #%s", contact.email, contact.id)
            return True
        except EmailSenderException as e:
            logger.error("Failed to send customer confirmation email for #%s: %s", contact.id, e.message)
            return False
        except Exception as e:
            logger.error("Unexpected error sending customer confirmation email for #%s: %s", contact.id, e, exc_info=True)
            return False
