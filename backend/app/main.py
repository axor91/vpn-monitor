"""FastAPI application entry point."""

import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers.monitor import router as monitor_router
from .services import checker, storage
from .services.xray import cleanup_temp_files

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("vpn.main")


def _scheduler_loop(data_store: dict, data_lock, save_fn):
    """Background loop: run check_all_sources every check_interval seconds."""
    while True:
        try:
            checker.check_all_sources(data_store, data_lock, save_fn)
        except Exception as e:
            log.error("Ошибка в планировщике: %s", e, exc_info=True)
        time.sleep(settings.check_interval)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    cleanup_temp_files()
    storage.load()

    data = storage.get_data()
    lock = storage.get_lock()

    t = threading.Thread(
        target=_scheduler_loop,
        args=(data, lock, storage.save),
        daemon=True,
    )
    t.start()
    log.info("Фоновый планировщик запущен (интервал: %d сек)", settings.check_interval)

    yield

    checker.request_stop()


app = FastAPI(
    title="VPN Monitor",
    version="2.0.0",
    docs_url=f"{settings.base_path}/api/docs",
    openapi_url=f"{settings.base_path}/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitor_router, prefix=settings.base_path)


@app.get("/health")
async def health():
    return {"status": "ok"}
