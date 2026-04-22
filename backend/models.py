from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


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
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )


class ApiTokens(Base):
    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    expire_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
