"""VPN link parsing — VLESS, VMess, Shadowsocks, Trojan."""

import base64
import json
import logging
import urllib.parse

log = logging.getLogger("vpn.parser")


def detect_protocol(link: str) -> str:
    for proto in ("vless", "vmess", "ss", "trojan", "hysteria2", "hy2", "tuic"):
        if link.lower().startswith(proto + "://"):
            return proto
    return "unknown"


def get_config_name(link: str) -> str:
    try:
        if "#" in link:
            return urllib.parse.unquote(link.split("#")[-1])
    except Exception:
        pass
    return "Config"


def parse_link(link: str) -> tuple[dict | None, str | None]:
    link = link.strip()
    proto = detect_protocol(link)
    parsers = {
        "vless": _parse_vless,
        "vmess": _parse_vmess,
        "ss": _parse_shadowsocks,
        "trojan": _parse_trojan,
    }
    if proto in parsers:
        return parsers[proto](link)
    return None, None


# ---------------------------------------------------------------------------
# VLESS
# ---------------------------------------------------------------------------
def _parse_vless(link: str) -> tuple[dict | None, str | None]:
    try:
        if not link.startswith("vless://"):
            return None, None
        part = link.replace("vless://", "")
        if "@" not in part:
            return None, None
        uuid_part, rest = part.split("@", 1)
        if "?" in rest:
            host_port, params_part = rest.split("?", 1)
        else:
            host_port, params_part = rest, ""
        if ":" not in host_port:
            return None, None
        address, port = host_port.rsplit(":", 1)
        port = port.split("/")[0]
        params = urllib.parse.parse_qs(params_part.split("#")[0])

        outbound = {
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": address,
                    "port": int(port),
                    "users": [{
                        "id": uuid_part,
                        "encryption": "none",
                        "flow": params.get("flow", [""])[0],
                    }],
                }]
            },
            "streamSettings": {
                "network": params.get("type", ["tcp"])[0],
                "security": params.get("security", ["none"])[0],
            },
        }
        security = outbound["streamSettings"]["security"]
        network = outbound["streamSettings"]["network"]

        if security == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "show": False,
                "fingerprint": params.get("fp", ["chrome"])[0],
                "serverName": params.get("sni", [""])[0],
                "publicKey": params.get("pbk", [""])[0],
                "shortId": params.get("sid", [""])[0],
                "spiderX": params.get("spx", [""])[0],
            }
        elif security == "tls":
            tls: dict = {
                "serverName": params.get("sni", [""])[0],
                "allowInsecure": True,
            }
            fp = params.get("fp", [""])[0]
            if fp:
                tls["fingerprint"] = fp
            alpn = params.get("alpn", [""])[0]
            if alpn:
                tls["alpn"] = alpn.split(",")
            outbound["streamSettings"]["tlsSettings"] = tls

        if network == "grpc":
            outbound["streamSettings"]["grpcSettings"] = {
                "serviceName": params.get("serviceName", [""])[0],
            }
        elif network == "ws":
            ws: dict = {"path": params.get("path", ["/"])[0]}
            host = params.get("host", [""])[0]
            if host:
                ws["headers"] = {"Host": host}
            outbound["streamSettings"]["wsSettings"] = ws
        elif network in ("xhttp", "splithttp"):
            outbound["streamSettings"]["xhttpSettings"] = {
                "path": params.get("path", ["/"])[0],
                "host": params.get("host", [""])[0],
            }
        elif network == "tcp":
            ht = params.get("headerType", ["none"])[0]
            if ht == "http":
                outbound["streamSettings"]["tcpSettings"] = {
                    "header": {
                        "type": "http",
                        "request": {
                            "path": [params.get("path", ["/"])[0]],
                            "headers": {"Host": [params.get("host", [""])[0]]},
                        },
                    }
                }
        return outbound, address
    except Exception as e:
        log.debug("parse_vless error: %s", e)
        return None, None


# ---------------------------------------------------------------------------
# VMess
# ---------------------------------------------------------------------------
def _parse_vmess(link: str) -> tuple[dict | None, str | None]:
    try:
        if not link.startswith("vmess://"):
            return None, None
        b64 = link.replace("vmess://", "").split("#")[0]
        b64 += "=" * (4 - len(b64) % 4) if len(b64) % 4 else ""
        data = json.loads(base64.b64decode(b64).decode("utf-8", errors="ignore"))
        address = data.get("add", "")
        port = int(data.get("port", 443))
        uid = data.get("id", "")
        aid = int(data.get("aid", 0))
        net = data.get("net", "tcp")
        tls = data.get("tls", "")
        sni = data.get("sni", data.get("host", ""))
        path = data.get("path", "/")
        host = data.get("host", "")

        outbound = {
            "protocol": "vmess",
            "settings": {
                "vnext": [{
                    "address": address,
                    "port": port,
                    "users": [{"id": uid, "alterId": aid, "security": "auto"}],
                }]
            },
            "streamSettings": {
                "network": net,
                "security": "tls" if tls == "tls" else "none",
            },
        }
        if tls == "tls":
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": sni,
                "allowInsecure": True,
            }
        if net == "ws":
            ws: dict = {"path": path}
            if host:
                ws["headers"] = {"Host": host}
            outbound["streamSettings"]["wsSettings"] = ws
        elif net == "grpc":
            outbound["streamSettings"]["grpcSettings"] = {
                "serviceName": data.get("path", ""),
            }
        return outbound, address
    except Exception as e:
        log.debug("parse_vmess error: %s", e)
        return None, None


# ---------------------------------------------------------------------------
# Shadowsocks
# ---------------------------------------------------------------------------
def _parse_shadowsocks(link: str) -> tuple[dict | None, str | None]:
    try:
        if not link.startswith("ss://"):
            return None, None
        part = link.replace("ss://", "")
        if "#" in part:
            part, _ = part.rsplit("#", 1)

        if "@" in part:
            user_info, server_part = part.rsplit("@", 1)
            try:
                user_info = base64.b64decode(user_info + "==").decode("utf-8", errors="ignore")
            except Exception:
                pass
            if ":" not in user_info:
                return None, None
            method, password = user_info.split(":", 1)
            host_port = server_part.split("?")[0].split("/")[0]
            address, port = host_port.rsplit(":", 1)
        else:
            try:
                decoded = base64.b64decode(
                    part.split("?")[0].split("/")[0] + "=="
                ).decode("utf-8", errors="ignore")
                if "@" not in decoded:
                    return None, None
                user_info, server_part = decoded.rsplit("@", 1)
                method, password = user_info.split(":", 1)
                address, port = server_part.rsplit(":", 1)
            except Exception:
                return None, None

        return {
            "protocol": "shadowsocks",
            "settings": {
                "servers": [{
                    "address": address,
                    "port": int(port),
                    "method": method,
                    "password": password,
                }]
            },
        }, address
    except Exception as e:
        log.debug("parse_shadowsocks error: %s", e)
        return None, None


# ---------------------------------------------------------------------------
# Trojan
# ---------------------------------------------------------------------------
def _parse_trojan(link: str) -> tuple[dict | None, str | None]:
    try:
        if not link.startswith("trojan://"):
            return None, None
        part = link.replace("trojan://", "")
        if "@" not in part:
            return None, None
        password, rest = part.split("@", 1)
        if "?" in rest:
            host_port, params_part = rest.split("?", 1)
        else:
            host_port, params_part = rest, ""
        host_port = host_port.split("/")[0]
        address, port = host_port.rsplit(":", 1)
        params = urllib.parse.parse_qs(params_part.split("#")[0])

        outbound = {
            "protocol": "trojan",
            "settings": {
                "servers": [{
                    "address": address,
                    "port": int(port),
                    "password": password,
                }]
            },
            "streamSettings": {
                "network": params.get("type", ["tcp"])[0],
                "security": params.get("security", ["tls"])[0],
            },
        }
        sni = params.get("sni", [""])[0]
        if outbound["streamSettings"]["security"] == "tls":
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": sni or address,
                "allowInsecure": True,
            }
        return outbound, address
    except Exception as e:
        log.debug("parse_trojan error: %s", e)
        return None, None
