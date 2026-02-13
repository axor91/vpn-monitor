"""Application configuration via environment variables."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8052
    debug: bool = False
    base_path: str = "/vpn-monitor"

    # Xray
    xray_path: str = os.path.join(os.path.dirname(__file__), "..", "xray", "xray")
    xray_startup_timeout: float = 5.0
    xray_test_timeout: float = 8.0

    # Ports for SOCKS proxies
    port_base: int = 10808
    port_range: int = 200

    # Checking
    max_configs_per_source: int = 150
    parallel_sources: int = 3
    parallel_tests: int = 6
    inter_test_delay: float = 0.3
    check_interval: int = 3600

    # Geo
    geo_cache_ttl: int = 3600

    # Rate limiting
    rate_limit_check: int = 2
    rate_limit_test: int = 5

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
