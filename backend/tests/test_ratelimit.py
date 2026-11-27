"""限流与访问防护。

注意：这些用例会真实触发限流，可能短暂封禁测试客户端 IP，
所以每个用例结束后要复位限流器的内存状态。
"""
import pytest

from app.core import ratelimit
from app.core.config import settings


@pytest.fixture()
def enable_rate_limit(monkeypatch):
    """打开限流，并在结束后清空令牌桶与封禁表。"""
    ratelimit._limiters.clear()
    ratelimit._limiters.update(
        {name: ratelimit.RateLimiter(rate, cap) for name, (rate, cap) in ratelimit.RULES.items()}
    )
    ratelimit._bans.clear()
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    yield
    ratelimit._limiters.clear()
    ratelimit._limiters.update(
        {name: ratelimit.RateLimiter(rate, cap) for name, (rate, cap) in ratelimit.RULES.items()}
    )
    ratelimit._bans.clear()


def test_auth_rate_limit(client, enable_rate_limit):
    """登录接口上限 6 次/分钟，第 7 次应 429。"""
    payload = {"username": "no_such_user", "password": "x"}
    codes = []
    for _ in range(8):
        resp = client.post("/api/v1/auth/login", json=payload)
        codes.append(resp.status_code)

    assert codes[:6] == [400] * 6 or all(code < 429 for code in codes[:6])
    assert codes[6] == 429
    assert codes[7] == 429


def test_429_response_shape(client, enable_rate_limit):
    payload = {"username": "no_such_user", "password": "x"}
    for _ in range(6):
        client.post("/api/v1/auth/login", json=payload)

    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 429
    body = resp.json()
    assert body["code"] == 429
    assert body["data"] is None
    assert "retry-after" in {k.lower() for k in resp.headers}


def test_script_ua_blocked(client, enable_rate_limit):
    resp = client.get(
        "/api/v1/books", headers={"User-Agent": "python-requests/2.31.0"}
    )
    assert resp.status_code == 429
    assert resp.json()["code"] == 429


def test_curl_ua_blocked(client, enable_rate_limit):
    resp = client.get("/api/v1/books", headers={"User-Agent": "curl/8.0.1"})
    assert resp.status_code == 429


def test_browser_ua_allowed(client, enable_rate_limit):
    resp = client.get(
        "/api/v1/books",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    assert resp.status_code == 200


def test_limit_disabled_by_default(client):
    """默认夹具关闭了限流：连续 20 次登录都不该 429。"""
    payload = {"username": "no_such_user", "password": "x"}
    for _ in range(20):
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code != 429
