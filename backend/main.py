from __future__ import annotations

import asyncio
import json
import logging
import math
import numbers
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from starlette.responses import JSONResponse
from starlette.responses import StreamingResponse

from .agent_workflow import run_agent_workflow
from .config import get_data_source_configs
from .database import SessionLocal, init_db
from .models import UserHolding, utc_now
from .stock_universe import get_universe_components, list_universes

logger = logging.getLogger(__name__)


class ScreenerRunRequest(BaseModel):
    query: str = Field(..., min_length=1, description="自然语言选股指令")
    universe: str = Field("local", description="股票池范围，例如 local/csi300/csi500/csi1000")


class ScreenerRunResponse(BaseModel):
    stock_pool: list[dict[str, Any]]
    final_report: str
    risk_assessment: str
    factor_summary: str = ""


class DataSourceStatus(BaseModel):
    name: str
    enabled: bool
    configured: bool
    base_url: str
    timeout_seconds: int


class DataSourcesResponse(BaseModel):
    sources: list[DataSourceStatus]


class UniverseOptionResponse(BaseModel):
    key: str
    label: str
    description: str
    index_code: str | None = None


class UniversePreviewResponse(BaseModel):
    key: str
    count: int
    stocks: list[dict[str, Any]]


class HoldingItem(BaseModel):
    ths_code: str = Field(..., min_length=1)
    sec_name: str = ""
    quantity: float = 0
    cost_price: float = 0
    latest_price: float = 0
    note: str = ""


class HoldingUploadRequest(BaseModel):
    holdings: list[HoldingItem]
    replace: bool = True


class HoldingUploadResponse(BaseModel):
    count: int
    holdings: list[dict[str, Any]]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Quant Screener Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/config/data-sources", response_model=DataSourcesResponse)
def get_data_sources() -> DataSourcesResponse:
    sources = [
        DataSourceStatus(
            name=item.name,
            enabled=item.enabled,
            configured=item.configured,
            base_url=item.base_url,
            timeout_seconds=item.timeout_seconds,
        )
        for item in get_data_source_configs()
    ]
    return DataSourcesResponse(sources=sources)


@app.get("/api/v1/universes", response_model=list[UniverseOptionResponse])
def get_universes() -> list[UniverseOptionResponse]:
    return [UniverseOptionResponse(**item) for item in list_universes()]


@app.get("/api/v1/universes/{universe_key}", response_model=UniversePreviewResponse)
def preview_universe(universe_key: str) -> UniversePreviewResponse:
    with SessionLocal() as db:
        df = get_universe_components(db, universe_key, persist=True)
    records = _sanitize_payload(df.head(80).to_dict(orient="records")) if not df.empty else []
    return UniversePreviewResponse(key=universe_key, count=int(len(df)), stocks=records)


def _normalize_holding_code(raw_code: str) -> str:
    code = raw_code.strip().upper()
    if "." in code:
        return code
    if code.startswith(("6", "9")):
        return f"{code}.SH"
    return f"{code}.SZ"


def _holding_to_record(row: UserHolding) -> dict[str, Any]:
    market_value = row.quantity * row.latest_price
    cost_value = row.quantity * row.cost_price
    pnl = market_value - cost_value
    pnl_pct = (pnl / cost_value * 100) if cost_value else 0.0
    return {
        "id": row.id,
        "ths_code": row.ths_code,
        "sec_name": row.sec_name,
        "quantity": row.quantity,
        "cost_price": row.cost_price,
        "latest_price": row.latest_price,
        "market_value": market_value,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "note": row.note,
        "updated_at": row.updated_at,
    }


@app.get("/api/v1/holdings", response_model=HoldingUploadResponse)
def list_holdings() -> HoldingUploadResponse:
    with SessionLocal() as db:
        rows = db.execute(select(UserHolding).order_by(UserHolding.id)).scalars().all()
    records = _sanitize_payload([_holding_to_record(row) for row in rows])
    return HoldingUploadResponse(count=len(records), holdings=records)


@app.post("/api/v1/holdings/upload", response_model=HoldingUploadResponse)
def upload_holdings(payload: HoldingUploadRequest) -> HoldingUploadResponse:
    with SessionLocal() as db:
        if payload.replace:
            db.execute(delete(UserHolding))

        for item in payload.holdings:
            ths_code = _normalize_holding_code(item.ths_code)
            existed = (
                db.execute(select(UserHolding).where(UserHolding.ths_code == ths_code))
                .scalars()
                .first()
            )
            if existed:
                existed.sec_name = item.sec_name or existed.sec_name
                existed.quantity = item.quantity
                existed.cost_price = item.cost_price
                existed.latest_price = item.latest_price
                existed.note = item.note
                existed.updated_at = utc_now()
            else:
                db.add(
                    UserHolding(
                        ths_code=ths_code,
                        sec_name=item.sec_name or ths_code.split(".")[0],
                        quantity=item.quantity,
                        cost_price=item.cost_price,
                        latest_price=item.latest_price,
                        note=item.note,
                    )
                )
        db.commit()
        rows = db.execute(select(UserHolding).order_by(UserHolding.id)).scalars().all()

    records = _sanitize_payload([_holding_to_record(row) for row in rows])
    return HoldingUploadResponse(count=len(records), holdings=records)


def _dataframe_to_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    df = state.get("stock_pool")
    if df is None or getattr(df, "empty", True):
        return []
    normalized = df.copy()
    for col in normalized.columns:
        normalized[col] = normalized[col].apply(_sanitize_value)
    return _sanitize_payload(normalized.to_dict(orient="records"))


def _sanitize_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    if isinstance(value, numbers.Real):
        try:
            num = float(value)
            if not math.isfinite(num):
                return None
            if isinstance(value, numbers.Integral):
                return int(value)
            return num
        except Exception:
            pass

    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except Exception:
            return str(value)

    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except Exception:
        pass

    return value


def _sanitize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: _sanitize_payload(v) for k, v in payload.items()}
    if isinstance(payload, (tuple, set)):
        return [_sanitize_payload(v) for v in payload]
    if isinstance(payload, list):
        return [_sanitize_payload(v) for v in payload]
    sanitized = _sanitize_value(payload)
    if isinstance(sanitized, (dict, list, tuple, set)):
        return _sanitize_payload(sanitized)
    return sanitized


@app.post("/api/v1/screener/run", response_model=ScreenerRunResponse)
def run_screener(payload: ScreenerRunRequest) -> ScreenerRunResponse:
    try:
        state = run_agent_workflow(payload.query, universe_key=payload.universe)
        result = _sanitize_payload(
            {
                "stock_pool": _dataframe_to_records(state),
                "final_report": state.get("final_report", ""),
                "risk_assessment": state.get("risk_assessment", ""),
                "factor_summary": state.get("factor_summary", ""),
            }
        )
        # Validate JSON serializability early, then return raw JSON response.
        json.dumps(result, ensure_ascii=False, allow_nan=False)
        return JSONResponse(content=result)
    except Exception as exc:
        logger.exception("run_screener failed for query=%r", payload.query)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {exc}") from exc


@app.get("/api/v1/screener/stream")
async def stream_screener(
    query: str = Query(..., min_length=1),
    universe: str = Query("local", min_length=1),
) -> StreamingResponse:
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit_event(event: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(event_queue.put_nowait, {"type": "progress", **event})

    def worker() -> None:
        try:
            state = run_agent_workflow(query, universe_key=universe, event_callback=emit_event)
            payload = {
                "type": "result",
                "stock_pool": _dataframe_to_records(state),
                "final_report": state.get("final_report", ""),
                "risk_assessment": state.get("risk_assessment", ""),
                "factor_summary": state.get("factor_summary", ""),
            }
            loop.call_soon_threadsafe(event_queue.put_nowait, payload)
        except Exception as exc:
            loop.call_soon_threadsafe(
                event_queue.put_nowait,
                {"type": "error", "message": f"Workflow execution failed: {exc}"},
            )
        finally:
            loop.call_soon_threadsafe(event_queue.put_nowait, {"type": "done"})

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    async def event_generator():
        while True:
            event = await event_queue.get()
            safe_event = _sanitize_payload(event)
            yield f"data: {json.dumps(safe_event, ensure_ascii=False, allow_nan=False)}\n\n"
            if event.get("type") == "done":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
