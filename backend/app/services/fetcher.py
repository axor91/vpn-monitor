"""Subscription fetcher — downloads and decodes VPN link lists."""

import base64
import logging

import httpx

log = logging.getLogger("vpn.fetcher")


def fetch_subscription(url: str) -> list[str]:
    """Download a subscription URL and return a list of VPN links."""
    try:
        r = httpx.get(url, timeout=15, follow_redirects=True)
        r.raise_for_status()
        text = r.text.strip()

        # Try base64 decode
        try:
            decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
            if "://" in decoded:
                text = decoded
        except Exception:
            pass

        return [line.strip() for line in text.splitlines() if "://" in line]
    except Exception as e:
        log.error("Ошибка загрузки %s: %s", url, e)
        return []
