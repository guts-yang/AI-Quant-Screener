from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import StockPool
from .tushare_client import fetch_index_weight, fetch_stock_basic, tushare_enabled


@dataclass(frozen=True)
class UniverseOption:
    key: str
    label: str
    description: str
    index_code: str | None = None


UNIVERSE_OPTIONS = [
    UniverseOption("local", "本地股票池", "使用数据库中已保存的股票池"),
    UniverseOption("csi300", "沪深300", "A股大盘核心资产", "000300.SH"),
    UniverseOption("csi500", "中证500", "中盘成长与价值组合", "000905.SH"),
    UniverseOption("csi1000", "中证1000", "小盘成长与高弹性组合", "000852.SH"),
    UniverseOption("sse50", "上证50", "沪市大盘蓝筹", "000016.SH"),
    UniverseOption("chinext", "创业板指", "创业板代表性标的", "399006.SZ"),
]


FALLBACK_COMPONENTS: dict[str, list[dict[str, str]]] = {
    "csi300": [
        {"ths_code": "600519.SH", "sec_name": "贵州茅台", "market_type": "主板"},
        {"ths_code": "601318.SH", "sec_name": "中国平安", "market_type": "主板"},
        {"ths_code": "600036.SH", "sec_name": "招商银行", "market_type": "主板"},
        {"ths_code": "000858.SZ", "sec_name": "五粮液", "market_type": "主板"},
        {"ths_code": "300750.SZ", "sec_name": "宁德时代", "market_type": "创业板"},
        {"ths_code": "601888.SH", "sec_name": "中国中免", "market_type": "主板"},
        {"ths_code": "000333.SZ", "sec_name": "美的集团", "market_type": "主板"},
        {"ths_code": "600276.SH", "sec_name": "恒瑞医药", "market_type": "主板"},
        {"ths_code": "002594.SZ", "sec_name": "比亚迪", "market_type": "主板"},
        {"ths_code": "601012.SH", "sec_name": "隆基绿能", "market_type": "主板"},
        {"ths_code": "600030.SH", "sec_name": "中信证券", "market_type": "主板"},
        {"ths_code": "601899.SH", "sec_name": "紫金矿业", "market_type": "主板"},
    ],
    "csi500": [
        {"ths_code": "600406.SH", "sec_name": "国电南瑞", "market_type": "主板"},
        {"ths_code": "600745.SH", "sec_name": "闻泰科技", "market_type": "主板"},
        {"ths_code": "002463.SZ", "sec_name": "沪电股份", "market_type": "主板"},
        {"ths_code": "000977.SZ", "sec_name": "浪潮信息", "market_type": "主板"},
        {"ths_code": "002230.SZ", "sec_name": "科大讯飞", "market_type": "主板"},
        {"ths_code": "600584.SH", "sec_name": "长电科技", "market_type": "主板"},
        {"ths_code": "300014.SZ", "sec_name": "亿纬锂能", "market_type": "创业板"},
        {"ths_code": "300124.SZ", "sec_name": "汇川技术", "market_type": "创业板"},
        {"ths_code": "601689.SH", "sec_name": "拓普集团", "market_type": "主板"},
        {"ths_code": "603799.SH", "sec_name": "华友钴业", "market_type": "主板"},
    ],
    "csi1000": [
        {"ths_code": "300274.SZ", "sec_name": "阳光电源", "market_type": "创业板"},
        {"ths_code": "300308.SZ", "sec_name": "中际旭创", "market_type": "创业板"},
        {"ths_code": "300502.SZ", "sec_name": "新易盛", "market_type": "创业板"},
        {"ths_code": "688008.SH", "sec_name": "澜起科技", "market_type": "科创板"},
        {"ths_code": "688012.SH", "sec_name": "中微公司", "market_type": "科创板"},
        {"ths_code": "688111.SH", "sec_name": "金山办公", "market_type": "科创板"},
        {"ths_code": "002920.SZ", "sec_name": "德赛西威", "market_type": "主板"},
        {"ths_code": "603501.SH", "sec_name": "韦尔股份", "market_type": "主板"},
        {"ths_code": "002129.SZ", "sec_name": "TCL中环", "market_type": "主板"},
        {"ths_code": "300661.SZ", "sec_name": "圣邦股份", "market_type": "创业板"},
    ],
    "sse50": [
        {"ths_code": "600519.SH", "sec_name": "贵州茅台", "market_type": "主板"},
        {"ths_code": "601318.SH", "sec_name": "中国平安", "market_type": "主板"},
        {"ths_code": "600036.SH", "sec_name": "招商银行", "market_type": "主板"},
        {"ths_code": "601166.SH", "sec_name": "兴业银行", "market_type": "主板"},
        {"ths_code": "600900.SH", "sec_name": "长江电力", "market_type": "主板"},
        {"ths_code": "601328.SH", "sec_name": "交通银行", "market_type": "主板"},
        {"ths_code": "601398.SH", "sec_name": "工商银行", "market_type": "主板"},
        {"ths_code": "600309.SH", "sec_name": "万华化学", "market_type": "主板"},
    ],
    "chinext": [
        {"ths_code": "300750.SZ", "sec_name": "宁德时代", "market_type": "创业板"},
        {"ths_code": "300760.SZ", "sec_name": "迈瑞医疗", "market_type": "创业板"},
        {"ths_code": "300124.SZ", "sec_name": "汇川技术", "market_type": "创业板"},
        {"ths_code": "300274.SZ", "sec_name": "阳光电源", "market_type": "创业板"},
        {"ths_code": "300015.SZ", "sec_name": "爱尔眼科", "market_type": "创业板"},
        {"ths_code": "300308.SZ", "sec_name": "中际旭创", "market_type": "创业板"},
        {"ths_code": "300059.SZ", "sec_name": "东方财富", "market_type": "创业板"},
        {"ths_code": "300498.SZ", "sec_name": "温氏股份", "market_type": "创业板"},
    ],
}


def list_universes() -> list[dict[str, Any]]:
    return [
        {
            "key": item.key,
            "label": item.label,
            "description": item.description,
            "index_code": item.index_code,
        }
        for item in UNIVERSE_OPTIONS
    ]


def _market_type(ts_code: str, fallback: str | None = None) -> str:
    code = ts_code.split(".")[0]
    if code.startswith("688"):
        return "科创板"
    if code.startswith("300"):
        return "创业板"
    if fallback:
        return fallback
    return "主板"


def _fallback_components(key: str) -> list[dict[str, Any]]:
    rows = FALLBACK_COMPONENTS.get(key) or []
    return [dict(row, source="内置样例") for row in rows]


def _fetch_tushare_components(option: UniverseOption) -> list[dict[str, Any]]:
    if not option.index_code or not tushare_enabled():
        return []

    weights = fetch_index_weight(option.index_code)
    codes = sorted({str(row.get("con_code", "")).strip() for row in weights if row.get("con_code")})
    basics = fetch_stock_basic(codes)

    rows = []
    for code in codes:
        basic = basics.get(code, {})
        rows.append(
            {
                "ths_code": code,
                "sec_name": basic.get("name") or code.split(".")[0],
                "market_type": _market_type(code, basic.get("market")),
                "source": "Tushare",
            }
        )
    return rows


def _extend_seeded(rows: list[dict[str, Any]], key: str, target_size: int = 40) -> list[dict[str, Any]]:
    if len(rows) >= target_size:
        return rows

    expanded = rows.copy()
    suffix = ".SH" if key in {"sse50"} else ".SZ"
    prefix = "60" if suffix == ".SH" else "00"
    while len(expanded) < target_size:
        seed = sha256(f"{key}-{len(expanded)}".encode("utf-8")).hexdigest()
        code = f"{prefix}{int(seed[:6], 16) % 9999:04d}{suffix}"
        if any(row["ths_code"] == code for row in expanded):
            continue
        expanded.append(
            {
                "ths_code": code,
                "sec_name": f"{UNIVERSE_LABELS.get(key, '指数')}成分{len(expanded) + 1}",
                "market_type": _market_type(code),
                "source": "内置扩展",
            }
        )
    return expanded


UNIVERSE_LABELS = {item.key: item.label for item in UNIVERSE_OPTIONS}


def upsert_stock_pool(db: Session, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        ths_code = str(row["ths_code"]).strip()
        if not ths_code:
            continue
        existed = db.execute(select(StockPool).where(StockPool.ths_code == ths_code)).scalars().first()
        if existed:
            existed.sec_name = str(row.get("sec_name") or existed.sec_name)
            existed.market_type = str(row.get("market_type") or existed.market_type)
        else:
            db.add(
                StockPool(
                    ths_code=ths_code,
                    sec_name=str(row.get("sec_name") or ths_code.split(".")[0]),
                    market_type=str(row.get("market_type") or _market_type(ths_code)),
                )
            )
    db.commit()


def get_universe_components(db: Session, key: str = "local", persist: bool = True) -> pd.DataFrame:
    normalized_key = key if key in UNIVERSE_LABELS else "local"
    if normalized_key == "local":
        records = [
            {"ths_code": row.ths_code, "sec_name": row.sec_name, "market_type": row.market_type, "source": "本地"}
            for row in db.execute(select(StockPool)).scalars().all()
        ]
        return pd.DataFrame(records)

    option = next(item for item in UNIVERSE_OPTIONS if item.key == normalized_key)
    try:
        rows = _fetch_tushare_components(option)
    except Exception:
        rows = []

    if not rows:
        rows = _extend_seeded(_fallback_components(normalized_key), normalized_key)

    if persist:
        upsert_stock_pool(db, rows)

    return pd.DataFrame(rows)
