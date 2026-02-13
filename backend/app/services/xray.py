"""Xray-core test runner with port management."""

import json
import logging
import os
import socket
import subprocess
import tempfile
import threading
import time
import uuid

import httpx

from ..config import settings
from .geo import get_geo_info

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


def run_test(outbound_config: dict, address: str) -> dict:
    """Start xray with the given outbound, test connectivity, return result."""
    port = _get_free_port()

    xray_config = {
        "log": {"loglevel": "error"},
        "inbounds": [{"port": port, "protocol": "socks", "settings": {"auth": "noauth"}}],
        "outbounds": [outbound_config],
    }

    tmp_dir = os.path.join(tempfile.gettempdir(), "vpn_monitor")
    os.makedirs(tmp_dir, exist_ok=True)
    config_path = os.path.join(tmp_dir, f"xray_{uuid.uuid4().hex[:8]}.json")
    proc = None

    try:
        with open(config_path, "w") as f:
            json.dump(xray_config, f)

        proc = subprocess.Popen(
            [settings.xray_path, "-c", config_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not _wait_for_port(port):
            return {"status": "error", "msg": "Xray не запустился"}

        proxy = f"socks5://127.0.0.1:{port}"
        for check_url in settings.check_urls:
            try:
                start = time.time()
                r = httpx.get(check_url, proxy=proxy, timeout=settings.xray_test_timeout)
                duration = round((time.time() - start) * 1000)
                if r.status_code in (200, 204):
                    geo = get_geo_info(address)
                    return {"status": "success", "latency": duration, "geo": geo}
            except Exception:
                continue

        return {"status": "error", "msg": "Не удалось подключиться"}

    except Exception as e:
        log.debug("run_test error for %s: %s", address, e)
        return {"status": "error", "msg": str(e)}

    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        try:
            os.remove(config_path)
        except OSError:
            pass


def cleanup_temp_files() -> None:
    """Remove stale temp configs from previous runs."""
    tmp_dir = os.path.join(tempfile.gettempdir(), "vpn_monitor")
    try:
        if os.path.isdir(tmp_dir):
            for f in os.listdir(tmp_dir):
                if f.startswith("xray_") and f.endswith(".json"):
                    try:
                        os.remove(os.path.join(tmp_dir, f))
                    except OSError:
                        pass
    except Exception:
        pass
