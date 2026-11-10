import ipaddress
from functools import lru_cache
from typing import List, Optional, Union
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.config import create_config

config = create_config()

DEFAULT_TRUSTED_PROXIES: List[str] = [
    "127.0.0.1",
    "::1",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
]


def _parse_network(net_str: str) -> Optional[Union[ipaddress.IPv4Network, ipaddress.IPv6Network]]:
    s = net_str.strip()
    if not s:
        return None
    if s.lower() == "localhost":
        return ipaddress.ip_network("127.0.0.1/32")
    try:
        return ipaddress.ip_network(s, strict=False)
    except ValueError:
        return None


@lru_cache(maxsize=128)
def _is_ip_in_trusted_networks(ip_str: str, networks_tuple: tuple[str, ...]) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    for net_str in networks_tuple:
        net = _parse_network(net_str)
        if net and addr in net:
            return True
    return False


def is_trusted_proxy(client_host: Optional[str], trusted_proxies: Optional[List[str]] = None) -> bool:
    """
    Проверяет, принадлежит ли IP адрес непосредственного подключения списку доверенных прокси/подсетей.
    """
    if not client_host:
        return False

    host = client_host.strip()
    if host.lower() == "testclient":
        return True

    if trusted_proxies is None:
        if hasattr(config, "rate_limit") and config.rate_limit.trusted_proxies:
            trusted_list = config.rate_limit.trusted_proxies
        else:
            trusted_list = DEFAULT_TRUSTED_PROXIES
    else:
        trusted_list = trusted_proxies

    return _is_ip_in_trusted_networks(host, tuple(trusted_list))


def _is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def get_real_client_ip(request: Request, trusted_proxies: Optional[List[str]] = None) -> str:
    """
    Получение реального IP клиента с защитой от подмены заголовков.
    
    Заголовки X-Real-IP и X-Forwarded-For считываются ТОЛЬКО в том случае,
    если непосредственный клиент (request.client.host) является доверенным прокси (trusted upstream).
    Если запрос поступил напрямую в обход доверенного прокси, заголовки игнорируются,
    что предотвращает обход лимитера и брутфорс авторизации.
    """
    direct_ip = get_remote_address(request)

    # Если прямое соединение не от доверенного прокси — не доверяем заголовкам
    if not is_trusted_proxy(direct_ip, trusted_proxies=trusted_proxies):
        return direct_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip and _is_valid_ip(real_ip):
        return real_ip.strip()

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ips = [ip.strip() for ip in forwarded.split(",") if ip.strip() and _is_valid_ip(ip.strip())]
        if ips:
            # Ищем первый справа IP, не входящий в доверенные прокси (клиент перед цепочкой прокси)
            for ip in reversed(ips):
                if not is_trusted_proxy(ip, trusted_proxies=trusted_proxies):
                    return ip
            return ips[0]

    return direct_ip


# Если в тестах — лимитер по умолчанию выключен, и используется in-memory хранилище
is_test_mode = config.env.mode == "TEST"

limiter = Limiter(
    key_func=get_real_client_ip,
    default_limits=["200/minute"],
    storage_uri="memory://" if is_test_mode else config.env.redis_url,
    enabled=not is_test_mode,
)
