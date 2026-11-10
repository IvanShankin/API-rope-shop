import pytest
from starlette.requests import Request
from src.core.rate_limit import get_real_client_ip


def _make_request(headers: dict, client_host: str = "127.0.0.1") -> Request:
    raw_headers = [(k.lower().encode("latin1"), v.encode("latin1")) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "client": (client_host, 12345),
    }
    return Request(scope)


def test_get_real_client_ip_prioritizes_x_real_ip():
    req = _make_request({
        "X-Real-IP": "203.0.113.195",
        "X-Forwarded-For": "1.2.3.4, 203.0.113.195",
    })
    assert get_real_client_ip(req) == "203.0.113.195"


def test_get_real_client_ip_uses_last_forwarded_ip_when_real_ip_absent():
    req = _make_request({
        "X-Forwarded-For": "1.2.3.4, 5.6.7.8, 198.51.100.22",
    })
    assert get_real_client_ip(req) == "198.51.100.22"


def test_get_real_client_ip_fallback_to_remote_address():
    req = _make_request({}, client_host="192.0.2.1")
    assert get_real_client_ip(req) == "192.0.2.1"


def test_get_real_client_ip_ignores_spoofed_headers_from_untrusted_client():
    """Атакующий напрямую обращается к сервису и подменяет заголовки — заголовки должны игнорироваться."""
    req = _make_request(
        {
            "X-Real-IP": "100.64.0.1",
            "X-Forwarded-For": "100.64.0.2, 100.64.0.3",
        },
        client_host="198.51.100.5",  # Внешний ненадежный IP
    )
    # Должен вернуться реальный IP прямого подключения, а не подставной из заголовков
    assert get_real_client_ip(req) == "198.51.100.5"


def test_get_real_client_ip_trusts_docker_internal_network():
    """Запрос через Nginx в Docker-сети (172.16.0.0/12) должен считывать X-Real-IP."""
    req = _make_request(
        {"X-Real-IP": "203.0.113.55"},
        client_host="172.18.0.2",
    )
    assert get_real_client_ip(req) == "203.0.113.55"


def test_get_real_client_ip_custom_trusted_proxies():
    """Проверка работы с кастомным списком доверенных прокси."""
    req = _make_request(
        {"X-Real-IP": "203.0.113.1"},
        client_host="198.51.100.99",
    )
    # Без указания прокси — 198.51.100.99 не доверен
    assert get_real_client_ip(req) == "198.51.100.99"

    # При явном доверии к 198.51.100.99 — читается X-Real-IP
    assert get_real_client_ip(req, trusted_proxies=["198.51.100.99"]) == "203.0.113.1"


def test_get_real_client_ip_invalid_x_real_ip_ignored():
    """Невалидный IP в X-Real-IP игнорируется, и берется IP из Forwarded или direct."""
    req = _make_request(
        {
            "X-Real-IP": "malicious_string_or_domain.com",
            "X-Forwarded-For": "203.0.113.77",
        },
        client_host="127.0.0.1",
    )
    assert get_real_client_ip(req) == "203.0.113.77"
