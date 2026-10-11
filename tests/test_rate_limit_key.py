"""La llave del rate limit usa X-Real-IP (Railway), no X-Forwarded-For."""
from starlette.requests import Request

from pharmatrack.utils.rate_limit import client_ip


def _req(headers):
    scope = {"type": "http", "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
             "client": ("10.0.0.1", 1234)}
    return Request(scope)


def test_client_ip_prefers_x_real_ip():
    assert client_ip(_req({"x-real-ip": "203.0.113.7", "x-forwarded-for": "1.2.3.4"})) == "203.0.113.7"
    assert client_ip(_req({})) == "10.0.0.1"
