from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class StockPool(Base):
    __tablename__ = "stock_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ths_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    sec_name: Mapped[str] = mapped_column(String(128), nullable=False)
    market_type: Mapped[str] = mapped_column(String(32), nullable=False, default="主板")


class FinancialData(Base):
    __tablename__ = "financial_data"
    __table_args__ = (
        UniqueConstraint("ths_code", "indicator_name", "report_date", name="uq_financial_data_unique"),
        Index("idx_financial_data_lookup", "ths_code", "indicator_name", "update_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ths_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    indicator_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    indicator_value: Mapped[float] = mapped_column(Float, nullable=False)
    report_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )


class FactorCharacteristic(Base):
    __tablename__ = "factor_characteristics"
    __table_args__ = (
        UniqueConstraint("ths_code", "as_of_date", name="uq_factor_characteristic_code_date"),
        Index("idx_factor_characteristic_lookup", "ths_code", "as_of_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ths_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    market_cap: Mapped[float] = mapped_column(Float, nullable=False)
    book_to_market: Mapped[float] = mapped_column(Float, nullable=False)
    operating_profitability: Mapped[float] = mapped_column(Float, nullable=False)
    asset_growth: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )


class FactorReturn(Base):
    __tablename__ = "factor_returns"
    __table_args__ = (
        UniqueConstraint("factor_date", "frequency", name="uq_factor_return_date_frequency"),
        Index("idx_factor_return_lookup", "factor_date", "frequency"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    factor_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, default="daily")
    mkt_rf: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    smb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    hml: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rmw: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cma: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rf: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )


class FactorExposure(Base):
    __tablename__ = "factor_exposures"
    __table_args__ = (
        UniqueConstraint("ths_code", "as_of_date", "window_days", name="uq_factor_exposure_code_date_window"),
        Index("idx_factor_exposure_lookup", "ths_code", "as_of_date", "window_days"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ths_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=252)
    alpha: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beta_mkt: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beta_smb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beta_hml: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beta_rmw: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    beta_cma: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    idiosyncratic_vol: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    r_squared: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )


class FactorScore(Base):
    __tablename__ = "factor_scores"
    __table_args__ = (
        UniqueConstraint("ths_code", "as_of_date", name="uq_factor_score_code_date"),
        Index("idx_factor_score_lookup", "ths_code", "as_of_date", "ff_rank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ths_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    as_of_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ff_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ff_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    factor_value_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    factor_profitability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    factor_investment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    factor_size_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    data_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )


class ScreeningRun(Base):
    __tablename__ = "screening_runs"
    __table_args__ = (Index("idx_screening_runs_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="ff5-proxy-v1")
    as_of_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    report_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )


class ApiTokens(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expire_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class UserHolding(Base):
    __tablename__ = "user_holdings"
    __table_args__ = (Index("idx_user_holdings_code", "ths_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ths_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    sec_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cost_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    latest_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        server_default=func.current_timestamp(),
    )
