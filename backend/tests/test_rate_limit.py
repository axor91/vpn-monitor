"""Tests for client-IP extraction trust boundary and the rate limiter."""

from types import SimpleNamespace

import app.routers.monitor as m


def _req(peer: str, headers: dict | None = None):
    return SimpleNamespace(
        client=SimpleNamespace(host=peer),
        headers={k.lower(): v for k, v in (headers or {}).items()},
    )


def test_trusted_peer_honours_real_ip():
    req = _req("127.0.0.1", {"X-Real-IP": "203.0.113.7"})
    assert m._get_client_ip(req) == "203.0.113.7"


def test_untrusted_peer_ignores_spoofed_header():
    # A direct (non-proxy) client cannot escape its real IP by spoofing headers.
    req = _req("203.0.113.9", {"X-Real-IP": "1.2.3.4", "X-Forwarded-For": "5.6.7.8"})
    assert m._get_client_ip(req) == "203.0.113.9"


def test_trusted_peer_falls_back_to_forwarded_for():
    req = _req("127.0.0.1", {"X-Forwarded-For": "198.51.100.4, 10.0.0.1"})
    assert m._get_client_ip(req) == "198.51.100.4"


def test_check_rate_blocks_over_limit():
    key = "test:unit-1"
    m._rate_limits.pop(key, None)
    assert m._check_rate(key, 2) is True
    assert m._check_rate(key, 2) is True
    assert m._check_rate(key, 2) is False  # third within window → blocked


def test_check_rate_gc_drops_stale_keys():
    # Seed a stale key with an old timestamp and force a GC pass.
    m._rate_limits["test:stale"] = [0.0]
    m._rate_last_gc = 0.0  # ensure the GC branch runs
    m._check_rate("test:fresh", 5)
    assert "test:stale" not in m._rate_limits
