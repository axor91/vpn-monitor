"""Tests for the SSRF outbound guard (IP-literal paths, no network)."""

import pytest

from app.services.netguard import resolve_global_ip


@pytest.mark.parametrize("addr", ["8.8.8.8", "1.1.1.1"])
def test_global_ipv4_allowed(addr):
    assert resolve_global_ip(addr) == addr


@pytest.mark.parametrize(
    "addr",
    [
        "127.0.0.1",      # loopback
        "10.0.0.1",       # private
        "192.168.1.10",   # private
        "169.254.1.1",    # link-local
        "::1",            # ipv6 loopback
        "[::1]",          # ipv6 loopback, bracketed literal
        "fd00::1",        # ipv6 unique-local
        "224.0.0.1",      # ipv4 multicast (is_global=True, must still block)
        "ff0e::1",        # ipv6 multicast
        "0.0.0.0",        # unspecified
    ],
)
def test_non_global_blocked(addr):
    assert resolve_global_ip(addr) is None


def test_global_ipv6_allowed():
    assert resolve_global_ip("2001:4860:4860::8888") == "2001:4860:4860::8888"


def test_bracketed_global_ipv6_allowed():
    assert resolve_global_ip("[2001:4860:4860::8888]") == "2001:4860:4860::8888"
