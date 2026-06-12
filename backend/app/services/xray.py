"""Proxy test runner with port management.

Dispatches to one of two engines based on the parsed config's `_engine` marker:
xray-core (vless/vmess/ss/trojan) or sing-box (hysteria2/tuic, QUIC-based).
Both spin up a local SOCKS inbound and probe connectivity through it.
"""

import copy
import json
import logging
import os
import socket
import subprocess
import tempfile
import threading
import time
import uuid
from typing import Any

import httpx

from ..config import settings
from .geo import get_geo_info
from .netguard import resolve_global_ip

log = logging.getLogger("vpn.xray")

_port_counter = 0
_port_lock = threading.Lock()


def _get_free_port() -> int:
    """Find a free port by attempting to bind."""
    global _port_counter
    with _port_lock:
        for _ in range(settings.port_range):
            port = settings.port_base + (_port_counter % settings.port_range)
            _port_counter += 1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free ports available")


def _wait_for_port(port: int, timeout: float | None = None) -> bool:
    """Poll until port is accepting connections."""
    timeout = timeout or settings.xray_startup_timeout
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                s.connect(("127.0.0.1", port))
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.15)
    return False


def _pin_xray_address(outbound: dict[str, Any], ip: str) -> None:
    """Replace server address with the already-validated IP so the engine cannot
    re-resolve the hostname to something else (DNS rebinding)."""
    s = outbound.get("settings", {})
    for server in s.get("vnext", []) + s.get("servers", []):
        server["address"] = ip


def _tmp_dir() -> str:
    d = os.path.join(tempfile.gettempdir(), "vpn_monitor")
    os.makedirs(d, exist_ok=True)
    return d


def _probe(port: int, ip: str) -> dict[str, Any]:
    """Probe connectivity through the local SOCKS proxy on `port`."""
    proxy = f"socks5://127.0.0.1:{port}"
    for check_url in settings.check_urls:
        try:
            start = time.time()
            r = httpx.get(check_url, proxy=proxy, timeout=settings.xray_test_timeout)
            duration = round((time.time() - start) * 1000)
            if r.status_code in (200, 204):
                return {"status": "success", "latency": duration, "geo": get_geo_info(ip)}
        except Exception:
            continue
    return {"status": "error", "msg": "Не удалось подключиться"}


def _terminate(proc: "subprocess.Popen[bytes]") -> None:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
        proc.wait()


def _run_engine(cmd: list[str], config: dict[str, Any], config_path: str, port: int, ip: str,
                engine_label: str) -> dict[str, Any]:
    """Write `config` to disk, launch `cmd`, wait for the SOCKS port, probe."""
    proc = None
    try:
        with open(config_path, "w") as f:
            json.dump(config, f)
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not _wait_for_port(port):
            return {"status": "error", "msg": f"{engine_label} не запустился"}
        return _probe(port, ip)
    except Exception as e:
        log.debug("run_test error (%s): %s", engine_label, e)
        return {"status": "error", "msg": str(e)}
    finally:
        if proc:
            _terminate(proc)
        try:
            os.remove(config_path)
        except OSError:
            pass


def _run_xray(outbound: dict[str, Any], port: int, ip: str) -> dict[str, Any]:
    _pin_xray_address(outbound, ip)
    xray_config = {
        "log": {"loglevel": "error"},
        "inbounds": [{"port": port, "protocol": "socks", "settings": {"auth": "noauth"}}],
        "outbounds": [outbound],
    }
    path = os.path.join(_tmp_dir(), f"xray_{uuid.uuid4().hex[:8]}.json")
    return _run_engine([settings.xray_path, "-c", path], xray_config, path, port, ip, "Xray")


def _run_singbox(outbound: dict[str, Any], port: int, ip: str) -> dict[str, Any]:
    outbound["server"] = ip  # pin resolved IP (DNS-rebinding guard)
    sb_config = {
        "log": {"level": "error"},
        "inbounds": [{"type": "socks", "listen": "127.0.0.1", "listen_port": port}],
        "outbounds": [outbound],
    }
    path = os.path.join(_tmp_dir(), f"singbox_{uuid.uuid4().hex[:8]}.json")
    return _run_engine([settings.singbox_path, "run", "-c", path], sb_config, path, port, ip,
                       "sing-box")


def run_test(config: dict[str, Any], address: str) -> dict[str, Any]:
    """Start the right engine for the parsed config, test connectivity, return result."""
    ip = resolve_global_ip(address)
    if ip is None:
        return {"status": "error", "msg": "Адрес не резолвится или запрещён"}
    config = copy.deepcopy(config)
    engine = config.pop("_engine", "xray")
    port = _get_free_port()
    if engine == "singbox":
        return _run_singbox(config, port, ip)
    return _run_xray(config, port, ip)


def cleanup_temp_files() -> None:
    """Remove stale temp configs from previous runs."""
    tmp_dir = os.path.join(tempfile.gettempdir(), "vpn_monitor")
    try:
        if os.path.isdir(tmp_dir):
            for f in os.listdir(tmp_dir):
                if (f.startswith("xray_") or f.startswith("singbox_")) and f.endswith(".json"):
                    try:
                        os.remove(os.path.join(tmp_dir, f))
                    except OSError:
                        pass
    except Exception:
        pass
