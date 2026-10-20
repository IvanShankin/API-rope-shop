from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import create_config

config = create_config()


def get_real_client_ip(request: Request) -> str:
    """
    Получение реального IP клиента с учётом Nginx/Cloudflare прокси.
    Берёт левый (первый) IP из X-Forwarded-For, если он есть.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Если в тестах — лимитер полностью выключен
is_test_mode = config.env.mode == "TEST"

limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200/minute"],
    storage_uri=config.env.redis_url,
    enabled=not is_test_mode,
)