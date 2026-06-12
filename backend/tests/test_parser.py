"""Tests for VPN link parsing — the protocol-format surface."""

import base64
import json

import pytest

from app.services.parser import (
    detect_protocol,
    extract_link_meta,
    get_config_name,
    parse_link,
)


def _vmess_link(payload: dict) -> str:
    raw = base64.b64encode(json.dumps(payload).encode()).decode()
    return f"vmess://{raw}"


@pytest.mark.parametrize(
    "link,expected",
    [
        ("vless://uuid@host:443", "vless"),
        ("VLESS://uuid@host:443", "vless"),  # case-insensitive
        ("vmess://eyJ9", "vmess"),
        ("ss://abc@host:8388", "ss"),
        ("trojan://pw@host:443", "trojan"),
        ("hysteria2://x@host:443", "hysteria2"),
        ("tuic://x@host:443", "tuic"),
        ("https://example.com", "unknown"),
    ],
)
def test_detect_protocol(link, expected):
    assert detect_protocol(link) == expected


def test_get_config_name_decodes_fragment():
    assert get_config_name("vless://x@h:443#My%20Server") == "My Server"
    assert get_config_name("vless://x@h:443") == "Config"


# --- VLESS ---------------------------------------------------------------


def test_vless_reality():
    link = (
        "vless://11111111-1111-1111-1111-111111111111@1.2.3.4:443"
        "?type=tcp&security=reality&sni=vk.com&pbk=PUBKEY&sid=ab&fp=chrome&flow=xtls-rprx-vision#R"
    )
    outbound, address = parse_link(link)
    assert address == "1.2.3.4"
    assert outbound["protocol"] == "vless"
    ss = outbound["streamSettings"]
    assert ss["security"] == "reality"
    assert ss["realitySettings"]["serverName"] == "vk.com"
    assert ss["realitySettings"]["publicKey"] == "PUBKEY"
    user = outbound["settings"]["vnext"][0]["users"][0]
    assert user["flow"] == "xtls-rprx-vision"
    assert outbound["settings"]["vnext"][0]["port"] == 443


def test_vless_tls_ws():
    link = (
        "vless://uuid@example.com:8443"
        "?type=ws&security=tls&sni=example.com&path=%2Fws&host=cdn.example.com&alpn=h2,http/1.1"
    )
    outbound, address = parse_link(link)
    assert address == "example.com"
    ss = outbound["streamSettings"]
    assert ss["security"] == "tls"
    assert ss["tlsSettings"]["serverName"] == "example.com"
    assert ss["tlsSettings"]["alpn"] == ["h2", "http/1.1"]
    assert ss["wsSettings"]["path"] == "/ws"
    assert ss["wsSettings"]["headers"]["Host"] == "cdn.example.com"


def test_vless_grpc():
    link = "vless://uuid@h:443?type=grpc&security=tls&serviceName=grpcsvc&sni=h"
    outbound, _ = parse_link(link)
    assert outbound["streamSettings"]["grpcSettings"]["serviceName"] == "grpcsvc"


def test_vless_missing_userinfo_returns_none():
    outbound, address = parse_link("vless://no-at-sign-here:443")
    assert outbound is None and address is None


# --- VMess ---------------------------------------------------------------


def test_vmess_ws_tls():
    link = _vmess_link({
        "add": "1.2.3.4", "port": "443", "id": "uuid", "aid": "0",
        "net": "ws", "tls": "tls", "host": "cdn.example.com", "path": "/p",
    })
    outbound, address = parse_link(link)
    assert address == "1.2.3.4"
    ss = outbound["streamSettings"]
    assert ss["security"] == "tls"
    assert ss["wsSettings"]["path"] == "/p"
    assert ss["wsSettings"]["headers"]["Host"] == "cdn.example.com"
    assert outbound["settings"]["vnext"][0]["port"] == 443


# --- Shadowsocks ---------------------------------------------------------


def test_ss_userinfo_base64():
    user = base64.b64encode(b"aes-256-gcm:secret").decode()
    link = f"ss://{user}@1.2.3.4:8388#name"
    outbound, address = parse_link(link)
    assert address == "1.2.3.4"
    server = outbound["settings"]["servers"][0]
    assert server["method"] == "aes-256-gcm"
    assert server["password"] == "secret"
    assert server["port"] == 8388


def test_ss_fully_base64():
    blob = base64.b64encode(b"aes-128-gcm:pw@5.6.7.8:1234").decode()
    link = f"ss://{blob}#name"
    outbound, address = parse_link(link)
    assert address == "5.6.7.8"
    assert outbound["settings"]["servers"][0]["method"] == "aes-128-gcm"


# --- Trojan --------------------------------------------------------------


def test_trojan_tls():
    link = "trojan://password@host.example:443?security=tls&sni=host.example#t"
    outbound, address = parse_link(link)
    assert address == "host.example"
    assert outbound["protocol"] == "trojan"
    assert outbound["settings"]["servers"][0]["password"] == "password"
    assert outbound["streamSettings"]["tlsSettings"]["serverName"] == "host.example"


# --- meta / unsupported --------------------------------------------------


def test_extract_meta_vless_reality():
    meta = extract_link_meta("vless://x@h:443?security=reality&sni=vk.com")
    assert meta == {"security": "reality", "sni": "vk.com"}


def test_unsupported_protocol_returns_none():
    outbound, address = parse_link("ssr://some-unsupported-blob")
    assert outbound is None and address is None


# --- Hysteria2 (sing-box engine) -----------------------------------------


def test_hysteria2_full():
    link = (
        "hysteria2://s3cret@1.2.3.4:443/"
        "?sni=example.com&insecure=1&obfs=salamander&obfs-password=op#node"
    )
    outbound, address = parse_link(link)
    assert address == "1.2.3.4"
    assert outbound["_engine"] == "singbox"
    assert outbound["type"] == "hysteria2"
    assert outbound["server_port"] == 443
    assert outbound["password"] == "s3cret"
    assert outbound["tls"] == {
        "enabled": True, "server_name": "example.com", "insecure": True,
    }
    assert outbound["obfs"] == {"type": "salamander", "password": "op"}


def test_hy2_alias_no_obfs_default_secure():
    outbound, address = parse_link("hy2://pw@host.example:8443?sni=host.example")
    assert address == "host.example"
    assert outbound["type"] == "hysteria2"
    assert "obfs" not in outbound
    assert outbound["tls"]["insecure"] is False
    assert outbound["tls"]["server_name"] == "host.example"


def test_hysteria2_sni_defaults_to_address():
    outbound, _ = parse_link("hysteria2://pw@5.6.7.8:443")
    assert outbound["tls"]["server_name"] == "5.6.7.8"


def test_hysteria2_missing_userinfo_returns_none():
    assert parse_link("hysteria2://host:443") == (None, None)


# --- TUIC (sing-box engine) ----------------------------------------------


def test_tuic_full():
    link = (
        "tuic://2dd61d93-75d8-4da4-ac0e-6aece7eac365:pass@1.2.3.4:443"
        "?congestion_control=bbr&alpn=h3&sni=example.com&allow_insecure=1#node"
    )
    outbound, address = parse_link(link)
    assert address == "1.2.3.4"
    assert outbound["_engine"] == "singbox"
    assert outbound["type"] == "tuic"
    assert outbound["server_port"] == 443
    assert outbound["uuid"] == "2dd61d93-75d8-4da4-ac0e-6aece7eac365"
    assert outbound["password"] == "pass"
    assert outbound["congestion_control"] == "bbr"
    assert outbound["tls"]["alpn"] == ["h3"]
    assert outbound["tls"]["insecure"] is True


def test_tuic_defaults():
    outbound, _ = parse_link("tuic://uuid:pw@host:443?sni=host")
    assert outbound["congestion_control"] == "cubic"  # default
    assert outbound["tls"]["alpn"] == ["h3"]           # default
    assert outbound["tls"]["insecure"] is False


def test_tuic_missing_password_returns_none():
    # userinfo must be uuid:password
    assert parse_link("tuic://just-uuid@host:443") == (None, None)


@pytest.mark.parametrize("link", ["", "garbage", "vless://", "ss://"])
def test_broken_links_dont_raise(link):
    # Must degrade gracefully, never throw.
    assert parse_link(link) == (None, None) or parse_link(link)[0] is None
