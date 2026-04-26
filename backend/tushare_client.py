from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import requests


TUSHARE_BASE_URL = os.getenv("TUSHARE_BASE_URL", "https://api.waditu.com")
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN", "")
TUSHARE_HTTP_TIMEOUT_SECONDS = int(os.getenv("TUSHARE_HTTP_TIMEOUT_SECONDS", "20"))


def _today() -> str:
    return datetime.now(UTC).strftime("%Y%m%d")


def tushare_enabled() -> bool:
    return bool(TUSHARE_TOKEN)


def tushare_query(api_name: str, params: dict[str, Any], fields: str = "") -> list[dict[str, Any]]:
    if not TUSHARE_TOKEN:
        raise RuntimeError("未配置 TUSHARE_TOKEN")

    payload = {
        "api_name": api_name,
        "token": TUSHARE_TOKEN,
        "params": params,
        "fields": fields,
    }
    response = requests.post(TUSHARE_BASE_URL, json=payload, timeout=TUSHARE_HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    raw = response.json()

    if raw.get("code") not in (0, None):
        raise RuntimeError(raw.get("msg") or f"Tushare {api_name} 请求失败")

    data = raw.get("data") or {}
    items = data.get("items") or []
    columns = data.get("fields") or []
    return [dict(zip(columns, item, strict=False)) for item in items]


def fetch_index_weight(index_code: str, trade_date: str | None = None) -> list[dict[str, Any]]:
    date = trade_date or _today()
    rows = tushare_query(
        "index_weight",
        {"index_code": index_code, "trade_date": date},
        "index_code,con_code,trade_date,weight",
    )
    if rows:
        return rows

    # Tushare may not have published today's weights yet. Querying without
    # trade_date gives the latest available rows for most accounts.
    return tushare_query(
        "index_weight",
        {"index_code": index_code},
        "index_code,con_code,trade_date,weight",
    )


def fetch_stock_basic(codes: list[str]) -> dict[str, dict[str, Any]]:
    if not codes:
        return {}

    rows = tushare_query(
        "stock_basic",
        {"list_status": "L"},
        "ts_code,symbol,name,area,industry,market,list_date",
    )
    wanted = set(codes)
    return {row["ts_code"]: row for row in rows if row.get("ts_code") in wanted}
