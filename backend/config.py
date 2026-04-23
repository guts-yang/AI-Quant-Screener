from __future__ import annotations

import os
from dataclasses import dataclass


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DataSourceConfig:
    name: str
    enabled: bool
    configured: bool
    base_url: str
    timeout_seconds: int


def get_data_source_configs() -> list[DataSourceConfig]:
    ifind_configured = bool(os.getenv("IFIND_REFRESH_TOKEN") or os.getenv("IFIND_ACCESS_TOKEN"))
    deepseek_configured = bool(os.getenv("DEEPSEEK_API_KEY"))
    tushare_configured = bool(os.getenv("TUSHARE_TOKEN"))
    tickflow_configured = bool(os.getenv("TICKFLOW_API_KEY"))

    return [
        DataSourceConfig(
            name="ifind",
            enabled=True,
            configured=ifind_configured,
            base_url=os.getenv("IFIND_BASE_URL", "https://quantapi.51ifind.com/api/v1"),
            timeout_seconds=int(os.getenv("IFIND_HTTP_TIMEOUT_SECONDS", "20")),
        ),
        DataSourceConfig(
            name="deepseek",
            enabled=True,
            configured=deepseek_configured,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout_seconds=int(os.getenv("DEEPSEEK_HTTP_TIMEOUT_SECONDS", "60")),
        ),
        DataSourceConfig(
            name="tushare",
            enabled=_to_bool(os.getenv("ENABLE_TUSHARE"), default=False),
            configured=tushare_configured,
            base_url=os.getenv("TUSHARE_BASE_URL", "https://api.waditu.com"),
            timeout_seconds=int(os.getenv("TUSHARE_HTTP_TIMEOUT_SECONDS", "20")),
        ),
        DataSourceConfig(
            name="tickflow",
            enabled=_to_bool(os.getenv("ENABLE_TICKFLOW"), default=False),
            configured=tickflow_configured,
            base_url=os.getenv("TICKFLOW_BASE_URL", "https://api.tickflow.com/v1"),
            timeout_seconds=int(os.getenv("TICKFLOW_HTTP_TIMEOUT_SECONDS", "20")),
        ),
    ]
