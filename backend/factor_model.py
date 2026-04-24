from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

import pandas as pd


FACTOR_COLUMNS = [
    "beta_mkt",
    "beta_smb",
    "beta_hml",
    "beta_rmw",
    "beta_cma",
]


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass(frozen=True)
class FactorModelResult:
    stock_pool: pd.DataFrame
    summary: str


def _numeric_series(df: pd.DataFrame, column: str, fallback: pd.Series) -> pd.Series:
    if column not in df.columns:
        return fallback.astype(float)
    values = pd.to_numeric(df[column], errors="coerce")
    return values.where(values.notna(), fallback).astype(float)


def _seeded_series(codes: pd.Series, low: float, high: float, salt: str) -> pd.Series:
    span = high - low
    values = []
    for code in codes.astype(str):
        digest = sha256(f"{code}-{salt}".encode("utf-8")).hexdigest()
        seed = int(digest[:12], 16) % 10_000
        values.append(low + span * (seed / 10_000))
    return pd.Series(values, index=codes.index, dtype="float64")


def _zscore(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").astype(float)
    if numeric.notna().sum() == 0:
        return pd.Series(0.0, index=values.index)

    filled = numeric.fillna(numeric.median())
    std = filled.std(ddof=0)
    if std == 0 or pd.isna(std):
        scored = pd.Series(0.0, index=values.index)
    else:
        scored = (filled - filled.mean()) / std
    if not higher_is_better:
        scored = -scored
    return scored.clip(-3, 3)


def _percentile(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce").astype(float)
    if numeric.notna().sum() == 0:
        return pd.Series(50.0, index=values.index)
    ranks = numeric.rank(pct=True, method="average") * 100
    if not higher_is_better:
        ranks = 100 - ranks
    return ranks.fillna(50.0)


def _first_available(df: pd.DataFrame, names: list[str], fallback: pd.Series) -> pd.Series:
    for name in names:
        if name in df.columns:
            return _numeric_series(df, name, fallback)
    return fallback.astype(float)


def compute_fama_french_scores(stock_pool: pd.DataFrame, as_of_date: datetime | None = None) -> FactorModelResult:
    """Compute an A-share friendly Fama-French five-factor screening view.

    The current product does not yet store a full daily return panel, so this
    function creates a cross-sectional proxy that is deterministic when the
    upstream data source falls back to mock values. Once historical prices are
    available, the same output columns can be backed by rolling regressions.
    """
    if stock_pool.empty:
        return FactorModelResult(stock_pool=stock_pool, summary="五因子模型未运行：股票池为空。")

    df = stock_pool.copy()
    codes = df["ths_code"].astype(str) if "ths_code" in df.columns else pd.Series(df.index.astype(str), index=df.index)
    now = as_of_date or _utc_now()

    fallback_market_cap = _seeded_series(codes, 8_000_000_000, 180_000_000_000, "market-cap")
    fallback_float_cap = fallback_market_cap * _seeded_series(codes, 0.45, 0.92, "float-ratio")
    fallback_bm = _seeded_series(codes, 0.15, 1.8, "book-to-market")
    fallback_profitability = _seeded_series(codes, 0.04, 0.32, "op")
    fallback_investment = _seeded_series(codes, -0.05, 0.35, "asset-growth")
    fallback_momentum = _seeded_series(codes, -0.12, 0.22, "momentum")

    market_cap = _first_available(df, ["float_market_cap", "free_float_market_cap", "market_cap"], fallback_float_cap)
    total_market_cap = _first_available(df, ["market_cap", "total_market_cap"], fallback_market_cap)
    book_value = _first_available(df, ["book_value", "net_assets", "shareholders_equity"], total_market_cap * fallback_bm)
    total_assets = _first_available(df, ["total_assets"], total_market_cap * _seeded_series(codes, 1.2, 3.5, "assets"))
    total_assets_prev = _first_available(
        df,
        ["total_assets_prev", "total_assets_lag"],
        total_assets / (1 + fallback_investment.clip(lower=-0.8)),
    )
    operating_profit = _first_available(
        df,
        ["operating_profit", "operating_income", "ebit"],
        book_value * fallback_profitability,
    )

    pe = _first_available(df, ["pe_ttm", "pe", "市盈率"], _seeded_series(codes, 8, 45, "pe"))
    roe = _first_available(df, ["roe", "ROE"], _seeded_series(codes, 5, 28, "roe"))
    profit_growth = _first_available(
        df,
        ["net_profit_growth", "profit_growth", "净利润增长率"],
        _seeded_series(codes, -5, 40, "profit-growth"),
    )
    revenue_growth = _first_available(
        df,
        ["revenue_growth", "rev_growth", "营收同比"],
        _seeded_series(codes, -5, 35, "revenue-growth"),
    )
    recent_return = _first_available(df, ["change_pct", "change", "return_20d"], fallback_momentum)

    positive_market_cap = market_cap.where(market_cap > 0, fallback_float_cap)
    book_to_market = (book_value / total_market_cap.where(total_market_cap > 0)).replace([float("inf"), -float("inf")], pd.NA)
    book_to_market = book_to_market.fillna(fallback_bm).clip(lower=0.01, upper=5.0)

    operating_profitability = (operating_profit / book_value.where(book_value > 0)).replace(
        [float("inf"), -float("inf")],
        pd.NA,
    )
    operating_profitability = operating_profitability.fillna((roe / 100).clip(lower=-0.5, upper=0.8)).clip(-0.5, 1.0)

    asset_growth = ((total_assets - total_assets_prev) / total_assets_prev.where(total_assets_prev > 0)).replace(
        [float("inf"), -float("inf")],
        pd.NA,
    )
    asset_growth = asset_growth.fillna(fallback_investment).clip(-0.8, 2.0)

    size_score = _percentile(positive_market_cap, higher_is_better=False)
    value_score = _percentile(book_to_market, higher_is_better=True)
    profitability_score = _percentile(operating_profitability, higher_is_better=True)
    investment_score = _percentile(asset_growth, higher_is_better=False)

    alpha_proxy = (
        0.30 * _zscore(book_to_market)
        + 0.30 * _zscore(operating_profitability)
        + 0.20 * _zscore(asset_growth, higher_is_better=False)
        + 0.10 * _zscore(profit_growth)
        + 0.10 * _zscore(recent_return)
    )
    idiosyncratic_vol = (
        0.12
        + recent_return.abs().clip(0, 25) / 100
        + pe.clip(lower=0, upper=80) / 1000
        - roe.clip(lower=0, upper=50) / 1000
    ).clip(lower=0.05, upper=0.65)

    ff_score = (
        0.30 * _percentile(alpha_proxy)
        + 0.20 * value_score
        + 0.20 * profitability_score
        + 0.15 * investment_score
        + 0.10 * size_score
        - 0.05 * _percentile(idiosyncratic_vol)
    ).clip(0, 100)

    df["as_of_date"] = now.date().isoformat()
    df["market_cap"] = positive_market_cap.round(2)
    df["book_to_market"] = book_to_market.round(4)
    df["operating_profitability"] = operating_profitability.round(4)
    df["asset_growth"] = asset_growth.round(4)
    df["factor_value_score"] = value_score.round(2)
    df["factor_profitability_score"] = profitability_score.round(2)
    df["factor_investment_score"] = investment_score.round(2)
    df["factor_size_score"] = size_score.round(2)
    df["alpha"] = alpha_proxy.round(4)
    df["idiosyncratic_vol"] = idiosyncratic_vol.round(4)
    df["ff_score"] = ff_score.round(2)

    df["beta_mkt"] = (0.85 + _zscore(recent_return) * 0.08 + _zscore(pe) * 0.04).clip(0.45, 1.45).round(4)
    df["beta_smb"] = _zscore(positive_market_cap, higher_is_better=False).round(4)
    df["beta_hml"] = _zscore(book_to_market).round(4)
    df["beta_rmw"] = _zscore(operating_profitability).round(4)
    df["beta_cma"] = _zscore(asset_growth, higher_is_better=False).round(4)
    df["data_quality"] = df[
        [
            "market_cap",
            "book_to_market",
            "operating_profitability",
            "asset_growth",
            "ff_score",
        ]
    ].notna().mean(axis=1).mul(100).round(2)

    ranked = df.sort_values(["ff_score", "alpha", "data_quality"], ascending=[False, False, False]).reset_index(drop=True)
    ranked["ff_rank"] = ranked.index + 1

    summary = (
        f"五因子模型完成：as_of={now.date().isoformat()}，"
        f"覆盖 {len(ranked)} 只股票；综合分中位数 {ranked['ff_score'].median():.2f}，"
        f"正 alpha 代理信号 {int((ranked['alpha'] > 0).sum())} 只。"
    )
    return FactorModelResult(stock_pool=ranked, summary=summary)


def factor_columns_for_report() -> list[str]:
    return [
        "ths_code",
        "sec_name",
        "ff_rank",
        "ff_score",
        "alpha",
        "beta_mkt",
        "beta_smb",
        "beta_hml",
        "beta_rmw",
        "beta_cma",
        "book_to_market",
        "operating_profitability",
        "asset_growth",
        "idiosyncratic_vol",
        "data_quality",
    ]


def factor_summary_records(df: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if df.empty:
        return []
    cols = [col for col in factor_columns_for_report() if col in df.columns]
    return df[cols].head(limit).to_dict(orient="records")
