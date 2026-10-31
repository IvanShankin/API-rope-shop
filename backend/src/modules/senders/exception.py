from src.modules.base.exception import ServiceException


class SenderException(ServiceException):
    """Базовое исключение для сервисов отправки сообщений."""
    default_message = "Sender error"


# --- Email Exceptions ---
class EmailSenderException(SenderException):
    """Базовое исключение сервиса отправки email."""
    default_message = "Email sending error"


class EmailNotConfiguredError(EmailSenderException):
    """Параметры SMTP не настроены в конфигурации окружения."""
    default_message = "SMTP credentials are not configured"


class EmailRecipientError(EmailSenderException):
    """Не указан или некорректен email получателя."""
    default_message = "Invalid or empty recipient email address"


class EmailConnectionError(EmailSenderException):
    """Сетевая ошибка или таймаут подключения к SMTP серверу."""
    default_message = "Could not connect to SMTP server"


class EmailAuthenticationError(EmailSenderException):
    """Ошибка аутентификации на SMTP сервере."""
    default_message = "SMTP authentication failed"


# --- Telegram Exceptions ---
class TelegramSenderException(SenderException):
    """Базовое исключение сервиса отправки Telegram сообщений."""
    default_message = "Telegram sending error"


class TelegramNotConfiguredError(TelegramSenderException):
    """TELEGRAM_BOT_TOKEN не настроен в конфигурации окружения."""
    default_message = "Telegram bot token is not configured"


class TelegramChatNotFoundError(TelegramSenderException):
    """Чат Telegram не найден (400 Bad Request: chat not found)."""
    default_message = "Telegram chat not found"


class TelegramForbiddenError(TelegramSenderException):
    """Бот не имеет прав на отправку в данный чат или заблокирован (403 Forbidden)."""
    default_message = "Telegram bot is forbidden from sending messages to this chat"


class TelegramRateLimitError(TelegramSenderException):
    """Превышен лимит запросов Telegram Bot API (429 Too Many Requests)."""
    default_message = "Telegram rate limit exceeded"


class TelegramNetworkError(TelegramSenderException):
    """Сетевая ошибка или таймаут соединения с Telegram Bot API."""
    default_message = "Network error connecting to Telegram Bot API"


class TelegramAPIError(TelegramSenderException):
    """Ошибка выполнения запроса к Telegram Bot API."""
    default_message = "Telegram Bot API error"
