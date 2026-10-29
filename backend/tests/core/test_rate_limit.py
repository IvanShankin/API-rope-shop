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
