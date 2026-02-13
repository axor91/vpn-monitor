"""Data persistence — JSON file storage with thread-safe access."""

import json
import logging
import os
import threading

from ..config import settings

log = logging.getLogger("vpn.storage")

_data: dict = {
    "last_update": None,
    "is_checking": False,
    "check_progress": {},
    "sources": {},
}
_lock = threading.Lock()


def get_data() -> dict:
    return _data


def get_lock() -> threading.Lock:
    return _lock


def save() -> None:
    """Persist data to disk atomically (temp file + rename)."""
    os.makedirs(settings.data_dir, exist_ok=True)
    path = os.path.join(settings.data_dir, settings.data_file)
    tmp_path = path + ".tmp"
    with _lock:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(_data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)


def load() -> None:
    """Load data from disk. Resets transient flags."""
    global _data
    path = os.path.join(settings.data_dir, settings.data_file)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _data.update(json.load(f))
            _data["is_checking"] = False
            _data["check_progress"] = {}
            log.info("Загружены данные из %s", path)
        except Exception:
            log.warning("Не удалось загрузить %s, начинаем с нуля", path)
