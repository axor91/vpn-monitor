"""Outbound address guard — SSRF protection for tested VPN configs."""

import ipaddress
import logging
import socket

log = logging.getLogger("vpn.netguard")


def resolve_global_ip(address: str) -> str | None:
    """Resolve an address (hostname or IPv4/IPv6 literal) and return the first
    globally-routable IP as a string.

    Returns None when the address does not resolve, or when ANY resolved
    record is non-global (private/loopback/link-local/reserved) — a single
    bad record blocks the whole host to defeat DNS-rebinding tricks.
    The returned IP is meant to be pinned into the Xray outbound so the
    check and the actual connection use the same resolution.
    """
    host = address.strip().strip("[]")
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        return None

    candidate: str | None = None
    for _family, _type, _proto, _canon, sockaddr in infos:
        try:
            ip = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            return None
        # is_global already excludes private/loopback/link-local/ULA, but some
        # multicast and reserved ranges report is_global=True — reject those too.
        if (
            not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            log.debug("Blocked non-routable address %s → %s", address, ip)
            return None
        if candidate is None:
            candidate = str(ip)
    return candidate
