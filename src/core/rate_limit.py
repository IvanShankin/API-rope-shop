from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import create_config

config = create_config()


def get_real_client_ip(request: Request) -> str:
    """
    Получение реального IP клиента с защитой от подмены заголовков.
    Приоритет:
    1. Заголовок X-Real-IP, устанавливаемый доверенным Nginx прокси из $remote_addr.
    2. Правый (последний) IP из X-Forwarded-For, добавленный доверенным прокси.
    3. Прямой IP соединения из ASGI scope (get_remote_address).
    """
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
        if ips:
            return ips[-1]

    return get_remote_address(request)


# Если в тестах — лимитер по умолчанию выключен, и используется in-memory хранилище
is_test_mode = config.env.mode == "TEST"

limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200/minute"],
    storage_uri="memory://" if is_test_mode else config.env.redis_url,
    enabled=not is_test_mode,
)
