"""Geolocation service with in-memory TTL cache."""

import logging
import socket
import threading
import time
from typing import Any

import httpx

from ..config import settings

log = logging.getLogger("vpn.geo")

_cache: dict[str, tuple[dict[str, Any], float]] = {}
_lock = threading.Lock()


def get_geo_info(address: str) -> dict[str, Any]:
    """Resolve IP and fetch geo data, with caching."""
    ip = address
    try:
        ip = socket.gethostbyname(address)
    except Exception as e:
        log.debug("DNS resolve failed for %s: %s", address, e)

    # Check cache
    with _lock:
        cached = _cache.get(ip)
        if cached and time.time() - cached[1] < settings.geo_cache_ttl:
            return cached[0]

    # Fetch
    try:
        url = f"https://ipwho.is/{ip}"
        data = httpx.get(url, timeout=4).json()
        if data.get("success"):
            result = {
                "country": data.get("country", "Unknown"),
                "code": data.get("country_code", "UN"),
                "isp": data.get("connection", {}).get("isp", data.get("isp", "Unknown")),
                "ip": data.get("ip", ip),
            }
            with _lock:
                _cache[ip] = (result, time.time())
            return result
        log.debug("Geo lookup failed for %s: %s", ip, data.get("message", "unknown"))
    except Exception as e:
        log.warning("Geo lookup error for %s: %s", address, e)

    return {"country": "Unknown", "code": "UN", "isp": "Unknown", "ip": address}


def clear_cache() -> int:
    """Clear the geo cache. Returns number of entries cleared."""
    with _lock:
        count = len(_cache)
        _cache.clear()
        return count
