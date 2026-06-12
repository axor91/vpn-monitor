"""API routes for VPN monitoring — status, results, summary, test link."""

import asyncio
import logging
import threading
import time
from collections import defaultdict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..config import settings
from ..models import StatusResponse, SummaryResponse, TestLinkRequest, TestResult
from ..services import storage
from ..services.parser import parse_link
from ..services.xray import run_test
from ..sources import SUBSCRIPTION_SOURCES

log = logging.getLogger("vpn.router")

router = APIRouter(prefix="/api")

# Rate limiting (keyed by real client IP)
_rate_limits: dict[str, list[float]] = defaultdict(list)
_rate_lock = threading.Lock()
_rate_last_gc = 0.0
_RATE_GC_INTERVAL = 300

# Backend is reachable only via the local reverse proxy (nginx / next rewrite),
# so X-Real-IP is trusted only when the TCP peer is loopback.
_TRUSTED_PEERS = {"127.0.0.1", "::1"}


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP.

    Honour X-Real-IP / X-Forwarded-For only when the TCP peer is the local
    reverse proxy; otherwise a client could spoof the header to dodge rate
    limits. Nginx overwrites X-Real-IP with $remote_addr.
    """
    peer = request.client.host if request.client else "unknown"
    if peer in _TRUSTED_PEERS:
        ip = request.headers.get("x-real-ip")
        if ip:
            return ip.strip()
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return peer


def _check_rate(key: str, limit: int) -> bool:
    """Sliding-window limiter. Periodically sweeps stale keys so spoofed or
    rotating IPs cannot grow the dict without bound."""
    global _rate_last_gc
    now = time.time()
    with _rate_lock:
        if now - _rate_last_gc >= _RATE_GC_INTERVAL:
            for k in [k for k, ts in _rate_limits.items() if not ts or now - ts[-1] >= 60]:
                del _rate_limits[k]
            _rate_last_gc = now
        _rate_limits[key] = [t for t in _rate_limits[key] if now - t < 60]
        if len(_rate_limits[key]) >= limit:
            return False
        _rate_limits[key].append(now)
        return True


@router.get("/status", response_model=StatusResponse)
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


@router.get("/summary", response_model=SummaryResponse)
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
            shutdown_ready = [
                c for c in alive if c.get("shutdown_ready")
            ]
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
                "shutdown_ready": len(shutdown_ready),
                "avg_latency": avg_latency,
                "fetched_at": src_data.get("fetched_at"),
            })
        summary["last_update"] = data.get("last_update")
        summary["is_checking"] = data.get("is_checking", False)
        summary["check_progress"] = data.get("check_progress", {})
    return summary


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


@router.post("/test_link", response_model=TestResult)
async def api_test_link(body: TestLinkRequest, request: Request):
    client_ip = _get_client_ip(request)
    if not _check_rate(f"test:{client_ip}", settings.rate_limit_test):
        return JSONResponse({"error": "Слишком много запросов"}, status_code=429)

    outbound, addr = parse_link(body.link)
    if not outbound or not addr:
        return JSONResponse(
            {"status": "error", "msg": "Неверная или неподдерживаемая ссылка"},
            status_code=422,
        )

    # SSRF guard (resolve + global-IP pinning) lives in run_test/netguard.
    result = await asyncio.to_thread(run_test, outbound, addr)
    return result
