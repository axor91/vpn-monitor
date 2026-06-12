"""Background checker — orchestrates parallel source checking."""

import concurrent.futures
import logging
import threading
import time
from datetime import datetime

from ..config import settings
from ..sources import SUBSCRIPTION_SOURCES
from ..whitelist_sni import is_whitelist_sni
from .fetcher import fetch_subscription
from .parser import detect_protocol, extract_link_meta, get_config_name, parse_link
from .xray import run_test

log = logging.getLogger("vpn.checker")

# Shared state
_stop_event = threading.Event()


def check_single_source(
    source_id: str,
    source_info: dict,
    data_store: dict,
    data_lock: threading.Lock,
) -> tuple[int, int]:
    """Check one subscription source. Returns (alive, total)."""
    log.info("Загружаем: %s (%s)", source_info["label"], source_id)
    links = fetch_subscription(source_info["url"])
    log.info("  [%s] Получено %d ссылок", source_id, len(links))
    links_to_check = links[: settings.max_configs_per_source]

    # Preserve old configs while checking
    with data_lock:
        old = data_store["sources"].get(source_id, {})
        data_store["sources"][source_id] = {
            "info": source_info,
            "configs": list(old.get("configs", [])),
            "total_links": len(links),
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "_checking": True,
        }

    new_configs = []
    alive = 0

    for i, link in enumerate(links_to_check):
        if _stop_event.is_set():
            log.info("  [%s] Остановлено пользователем", source_id)
            break

        with data_lock:
            data_store["check_progress"][source_id] = {
                "current": i + 1,
                "total": len(links_to_check),
                "source": source_info["label"],
            }

        proto = detect_protocol(link)
        name = get_config_name(link)
        outbound, address = parse_link(link)
        meta = extract_link_meta(link)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        shutdown_ready = (
            meta["security"] == "reality" and is_whitelist_sni(meta["sni"])
        )

        entry = {
            "link": link,
            "name": name,
            "protocol": proto,
            "address": address or "?",
            "status": "skip",
            "latency": None,
            "geo": None,
            "checked_at": now_str,
            "security": meta["security"],
            "sni": meta["sni"],
            "shutdown_ready": shutdown_ready,
        }

        if outbound and address:
            log.info(
                "  [%s] [%d/%d] %s://%s (%s)",
                source_id, i + 1, len(links_to_check), proto, address, name,
            )
            test_result = run_test(outbound, address)
            entry["status"] = test_result["status"]
            if test_result["status"] == "success":
                entry["latency"] = test_result["latency"]
                entry["geo"] = test_result["geo"]
                alive += 1
            else:
                entry["error"] = test_result.get("msg", "")
            time.sleep(settings.inter_test_delay)
        else:
            entry["status"] = "unsupported"
            if proto in ("hysteria2", "hy2", "tuic"):
                entry["error"] = f"Протокол {proto} не поддерживается"
            else:
                entry["error"] = "Ошибка парсинга"

        new_configs.append(entry)
        with data_lock:
            data_store["sources"][source_id]["configs"] = list(new_configs)

    # Finalize
    with data_lock:
        data_store["sources"][source_id]["configs"] = new_configs
        data_store["sources"][source_id].pop("_checking", None)
        data_store["check_progress"].pop(source_id, None)

    log.info("  [%s] Завершено: %d/%d живых", source_id, alive, len(new_configs))
    return alive, len(new_configs)


def check_all_sources(
    data_store: dict,
    data_lock: threading.Lock,
    save_fn,
) -> None:
    """Run a full check of all subscription sources."""
    with data_lock:
        if data_store["is_checking"]:
            log.warning("Проверка уже запущена, пропускаем")
            return
        data_store["is_checking"] = True
        data_store["check_progress"] = {}
    _stop_event.clear()

    try:
        log.info("=== Начинаем полную проверку подписок ===")
        source_items = list(SUBSCRIPTION_SOURCES.items())
        total_alive = 0
        total_configs = 0

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=settings.parallel_sources
        ) as pool:
            futures = {}
            for _idx, (source_id, source_info) in enumerate(source_items):
                f = pool.submit(
                    check_single_source, source_id, source_info, data_store, data_lock,
                )
                futures[f] = source_id

            for f in concurrent.futures.as_completed(futures):
                sid = futures[f]
                try:
                    a, t = f.result()
                    total_alive += a
                    total_configs += t
                except Exception as e:
                    log.error("Ошибка проверки %s: %s", sid, e, exc_info=True)

        log.info("=== Проверка завершена: %d/%d живых ===", total_alive, total_configs)
    except Exception as e:
        log.error("Критическая ошибка в check_all_sources: %s", e, exc_info=True)
    finally:
        with data_lock:
            data_store["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data_store["is_checking"] = False
            data_store["check_progress"] = {}
            # Drop persisted sources that are no longer configured.
            stale = [s for s in data_store["sources"] if s not in SUBSCRIPTION_SOURCES]
            for s in stale:
                del data_store["sources"][s]
        save_fn()


def request_stop() -> bool:
    """Request the checker to stop. Returns True if a check was running."""
    _stop_event.set()
    return True
