from __future__ import annotations

from backend.database import init_db, SessionLocal
from backend.models import StockPool

DEFAULT_STOCKS = [
    {"ths_code": "600519.SH", "sec_name": "贵州茅台", "market_type": "主板"},
    {"ths_code": "300750.SZ", "sec_name": "宁德时代", "market_type": "创业板"},
    {"ths_code": "688981.SH", "sec_name": "中芯国际", "market_type": "科创板"},
    {"ths_code": "000858.SZ", "sec_name": "五粮液", "market_type": "主板"},
    {"ths_code": "601318.SH", "sec_name": "中国平安", "market_type": "主板"},
]


def seed_stock_pool() -> None:
    with SessionLocal() as db:
        exists = db.query(StockPool).first()
        if exists:
            return
        db.add_all(StockPool(**row) for row in DEFAULT_STOCKS)
        db.commit()


if __name__ == "__main__":
    init_db()
    seed_stock_pool()
    print("Database initialized: quant_system.db")
