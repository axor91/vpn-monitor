"""API routes for VPN monitoring — status, results, summary, check control."""

import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..models import StatusResponse, SummaryResponse, TestLinkRequest
from ..sources import SUBSCRIPTION_SOURCES
from ..services import storage, checker
from ..services.parser import parse_link
from ..services.xray import run_test

router = APIRouter(prefix="/api")

# Rate limiting
_rate_limits: dict[str, list[float]] = defaultdict(list)
_rate_lock = threading.Lock()


def _check_rate(ip: str, limit: int) -> bool:
    now = time.time()
    with _rate_lock:
        _rate_limits[ip] = [t for t in _rate_limits[ip] if now - t < 60]
        if len(_rate_limits[ip]) >= limit:
            return False
        _rate_limits[ip].append(now)
        return True


@router.get("/status")
async def api_status():
    data = storage.get_data()
    lock = storage.get_lock()
    with lock:
        return StatusResponse(
            last_update=data.get("last_update"),
            is_checking=data.get("is_checking", False),
            check_progress=data.get("check_progress", {}),
            sources_count=len(data.get("sources", {})),
        )


@router.get("/summary")
async def api_summary():
    data = storage.get_data()
    lock = storage.get_lock()
    with lock:
        summary: dict = {"black": [], "white": []}
        for source_id, source_info in SUBSCRIPTION_SOURCES.items():
            src_data = data["sources"].get(source_id, {})
            configs = src_data.get("configs", [])
            alive = [c for c in configs if c.get("status") == "success"]
            dead = [c for c in configs if c.get("status") == "error"]
            unsupported = [c for c in configs if c.get("status") == "unsupported"]
            avg_latency = (
                round(sum(c["latency"] for c in alive) / len(alive)) if alive else 0
            )
            summary[source_info["category"]].append({
                "id": source_id,
                "label": source_info["label"],
                "description": source_info["description"],
                "category": source_info["category"],
                "total_links": src_data.get("total_links", 0),
                "checked": len(configs),
                "alive": len(alive),
                "dead": len(dead),
                "unsupported": len(unsupported),
                "avg_latency": avg_latency,
                "fetched_at": src_data.get("fetched_at"),
            })
        summary["last_update"] = data.get("last_update")
        summary["is_checking"] = data.get("is_checking", False)
        summary["check_progress"] = data.get("check_progress", {})
    return summary


@router.get("/results")
async def api_results():
    data = storage.get_data()
    lock = storage.get_lock()
    with lock:
        return data.get("sources", {})


@router.get("/results/{source_id}")
async def api_results_source(source_id: str):
    data = storage.get_data()
    lock = storage.get_lock()
    with lock:
        source = data["sources"].get(source_id)
        if not source:
            return JSONResponse({"error": "Источник не найден"}, status_code=404)
        return source


@router.get("/sources")
async def api_sources():
    return SUBSCRIPTION_SOURCES


@router.post("/start_check")
async def api_start_check(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate(f"check:{client_ip}", settings.rate_limit_check):
        return JSONResponse({"error": "Слишком много запросов"}, status_code=429)

    data = storage.get_data()
    lock = storage.get_lock()
    with lock:
        if data["is_checking"]:
            return JSONResponse({"error": "Проверка уже запущена"}, status_code=409)
        data["is_checking"] = True

    threading.Thread(
        target=checker.check_all_sources,
        args=(data, lock, storage.save),
        kwargs={"_from_api": True},
        daemon=True,
    ).start()
    return {"status": "ok", "msg": "Проверка запущена"}


@router.post("/stop_check")
async def api_stop_check():
    data = storage.get_data()
    if not data.get("is_checking"):
        return JSONResponse({"error": "Проверка не запущена"}, status_code=409)
    checker.request_stop()
    return {"status": "ok", "msg": "Остановка запрошена"}


@router.post("/test_link")
async def api_test_link(body: TestLinkRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate(f"test:{client_ip}", settings.rate_limit_test):
        return JSONResponse({"error": "Слишком много запросов"}, status_code=429)

    outbound, addr = parse_link(body.link)
    if not outbound:
        return {"status": "error", "msg": "Неверная или неподдерживаемая ссылка"}

    import asyncio
    result = await asyncio.to_thread(run_test, outbound, addr)
    return result
