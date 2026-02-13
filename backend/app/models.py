"""Pydantic models for API requests/responses."""

from pydantic import BaseModel


class TestLinkRequest(BaseModel):
    link: str


class TestResult(BaseModel):
    status: str
    latency: int | None = None
    geo: dict | None = None
    msg: str | None = None


class ConfigEntry(BaseModel):
    link: str
    name: str
    protocol: str
    address: str
    status: str
    latency: int | None = None
    geo: dict | None = None
    error: str | None = None
    checked_at: str | None = None


class SourceData(BaseModel):
    info: dict
    configs: list[ConfigEntry] = []
    total_links: int = 0
    fetched_at: str | None = None


class SourceSummary(BaseModel):
    id: str
    label: str
    description: str
    category: str
    total_links: int = 0
    checked: int = 0
    alive: int = 0
    dead: int = 0
    unsupported: int = 0
    avg_latency: int = 0
    fetched_at: str | None = None


class SummaryResponse(BaseModel):
    black: list[SourceSummary] = []
    white: list[SourceSummary] = []
    last_update: str | None = None
    is_checking: bool = False
    check_progress: dict = {}


class StatusResponse(BaseModel):
    last_update: str | None = None
    is_checking: bool = False
    check_progress: dict = {}
    sources_count: int = 0
