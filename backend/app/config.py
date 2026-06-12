"""Application configuration via environment variables."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "127.0.0.1"
    port: int = 8052
    debug: bool = False
    base_path: str = "/vpn-monitor"

    # Proxy engines
    xray_path: str = os.path.join(os.path.dirname(__file__), "..", "xray", "xray")
    # sing-box handles hysteria2/tuic (QUIC) which xray-core 1.8.24 can't.
    singbox_path: str = os.path.join(os.path.dirname(__file__), "..", "singbox", "sing-box")
    xray_startup_timeout: float = 5.0
    xray_test_timeout: float = 8.0

    # Ports for SOCKS proxies
    port_base: int = 10808
    port_range: int = 200

    # Checking
    max_configs_per_source: int = 150
    parallel_sources: int = 3
    inter_test_delay: float = 0.3
    check_interval: int = 21600

    # Geo
    geo_cache_ttl: int = 3600

    # Rate limiting (per real client IP, requests per minute)
    rate_limit_test: int = 20

    # Data
    data_dir: str = os.path.join(os.path.dirname(__file__), "..", "data")
    data_file: str = "vpn_data.json"

    # Check URLs
    check_urls: list[str] = [
        "https://www.google.com/generate_204",
        "https://cp.cloudflare.com",
        "https://www.gstatic.com/generate_204",
    ]

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:3052"
    cors_origins: list[str] = ["http://localhost:3052", "https://lmtools.ru"]

    model_config = {"env_prefix": "VPN_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
