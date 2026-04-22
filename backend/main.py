from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from .agent_workflow import run_agent_workflow
from .database import init_db


class ScreenerRunRequest(BaseModel):
    query: str = Field(..., min_length=1, description="自然语言选股指令")


class ScreenerRunResponse(BaseModel):
    stock_pool: list[dict[str, Any]]
    final_report: str
    risk_assessment: str


app = FastAPI(title="AI Quant Screener Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/v1/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _dataframe_to_records(state: dict[str, Any]) -> list[dict[str, Any]]:
    df = state.get("stock_pool")
    if df is None or getattr(df, "empty", True):
        return []
    normalized = df.copy()
    for col in normalized.columns:
        normalized[col] = normalized[col].apply(
            lambda x: x.isoformat() if hasattr(x, "isoformat") else x
        )
    return normalized.to_dict(orient="records")


@app.post("/api/v1/screener/run", response_model=ScreenerRunResponse)
def run_screener(payload: ScreenerRunRequest) -> ScreenerRunResponse:
    try:
        state = run_agent_workflow(payload.query)
        return ScreenerRunResponse(
            stock_pool=_dataframe_to_records(state),
            final_report=state.get("final_report", ""),
            risk_assessment=state.get("risk_assessment", ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {exc}") from exc


@app.get("/api/v1/screener/stream")
async def stream_screener(query: str = Query(..., min_length=1)) -> StreamingResponse:
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def emit_event(event: dict[str, Any]) -> None:
        loop.call_soon_threadsafe(event_queue.put_nowait, {"type": "progress", **event})

    def worker() -> None:
        try:
            state = run_agent_workflow(query, event_callback=emit_event)
            payload = {
                "type": "result",
                "stock_pool": _dataframe_to_records(state),
                "final_report": state.get("final_report", ""),
                "risk_assessment": state.get("risk_assessment", ""),
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
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("type") == "done":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
