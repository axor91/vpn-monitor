"""Subscription fetcher — downloads and decodes VPN link lists."""

import base64
import logging

import httpx

log = logging.getLogger("vpn.fetcher")


# Cap the download so a misbehaving/compromised source can't exhaust memory.
MAX_SUBSCRIPTION_BYTES = 8 * 1024 * 1024


def fetch_subscription(url: str) -> list[str]:
    """Download a subscription URL and return a list of VPN links."""
    try:
        with httpx.stream("GET", url, timeout=15, follow_redirects=True) as r:
            r.raise_for_status()
            chunks: list[bytes] = []
            total = 0
            for chunk in r.iter_bytes():
                total += len(chunk)
                if total > MAX_SUBSCRIPTION_BYTES:
                    log.warning("Подписка %s превышает лимит %d байт, обрезаем",
                                url, MAX_SUBSCRIPTION_BYTES)
                    break
                chunks.append(chunk)
        text = b"".join(chunks).decode("utf-8", errors="ignore").strip()

        # Try base64 decode
        try:
            decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
            if "://" in decoded:
                text = decoded
        except Exception:
            pass

        return [line.strip() for line in text.splitlines() if "://" in line]
    except Exception as e:
        log.warning("Ошибка загрузки %s: %s", url, e, exc_info=True)
        return []
