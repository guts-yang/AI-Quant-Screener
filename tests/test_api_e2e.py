from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd
from fastapi.testclient import TestClient

from backend import main as main_module


def _mock_workflow(query: str, event_callback: Any = None) -> dict[str, Any]:
    if event_callback:
        event_callback(
            {
                "agent": "DataAgent",
                "status": "running",
                "message": "Data agent is fetching data.",
                "think": "",
                "timestamp": "2026-01-01T00:00:00",
            }
        )
        event_callback(
            {
                "agent": "CIOAgent",
                "status": "done",
                "message": "CIO report is ready.",
                "think": "<think>Reasoning trace</think>",
                "timestamp": "2026-01-01T00:00:01",
            }
        )

    df = pd.DataFrame(
        [
            {
                "ths_code": "600519.SH",
                "sec_name": "Kweichow Moutai",
                "market_type": "MainBoard",
                "pe_ttm": 23.5,
                "net_profit_growth": 16.2,
                "report_date": "2025-12-31",
            }
        ]
    )
    return {
        "user_query": query,
        "stock_pool": df,
        "risk_assessment": "Risk is neutral.",
        "final_report": "# CIO Report\n\nBuild positions in batches.",
    }


def _mock_workflow_with_nan(query: str, event_callback: Any = None) -> dict[str, Any]:
    if event_callback:
        event_callback(
            {
                "agent": "DataAgent",
                "status": "done",
                "message": "Data includes NaN/Inf values.",
                "think": "",
                "timestamp": "2026-01-01T00:00:00",
            }
        )

    df = pd.DataFrame(
        [
            {
                "ths_code": "600519.SH",
                "pe_ttm": math.nan,
                "net_profit_growth": math.inf,
            }
        ]
    )
    return {
        "user_query": query,
        "stock_pool": df,
        "risk_assessment": "Risk is neutral.",
        "final_report": "# CIO Report",
    }


def _build_client(monkeypatch: Any) -> TestClient:
    monkeypatch.setattr(main_module, "init_db", lambda: None)
    return TestClient(main_module.app)


def test_run_endpoint_returns_stock_pool_and_report(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow)
    with _build_client(monkeypatch) as client:
        response = client.post("/api/v1/screener/run", json={"query": "find quality main-board stocks"})

    assert response.status_code == 200
    payload = response.json()
    assert "stock_pool" in payload
    assert "final_report" in payload
    assert "risk_assessment" in payload
    assert len(payload["stock_pool"]) == 1


def test_data_sources_endpoint_returns_source_status(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow)
    with _build_client(monkeypatch) as client:
        response = client.get("/api/v1/config/data-sources")

    assert response.status_code == 200
    payload = response.json()
    assert "sources" in payload
    assert isinstance(payload["sources"], list)
    names = {item["name"] for item in payload["sources"]}
    assert {"ifind", "deepseek", "tushare", "tickflow"}.issubset(names)


def test_run_endpoint_sanitizes_nan_and_inf(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow_with_nan)
    with _build_client(monkeypatch) as client:
        response = client.post("/api/v1/screener/run", json={"query": "nan test"})

    assert response.status_code == 200
    payload = response.json()
    row = payload["stock_pool"][0]
    assert row["pe_ttm"] is None
    assert row["net_profit_growth"] is None


def test_stream_endpoint_emits_progress_result_and_done(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow)
    with _build_client(monkeypatch) as client:
        with client.stream("GET", "/api/v1/screener/stream", params={"query": "find quality main-board stocks"}) as response:
            assert response.status_code == 200
            events: list[dict[str, Any]] = []
            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                events.append(json.loads(line[6:]))
                if events[-1].get("type") == "done":
                    break

    event_types = [event.get("type") for event in events]
    assert "progress" in event_types
    assert "result" in event_types
    assert event_types[-1] == "done"

    cio_events = [event for event in events if event.get("agent") == "CIOAgent"]
    assert cio_events
    assert "think" in cio_events[-1]


def test_stream_endpoint_sanitizes_nan_and_inf(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow_with_nan)
    with _build_client(monkeypatch) as client:
        with client.stream("GET", "/api/v1/screener/stream", params={"query": "nan test"}) as response:
            assert response.status_code == 200
            result_event: dict[str, Any] | None = None
            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if event.get("type") == "result":
                    result_event = event
                if event.get("type") == "done":
                    break

    assert result_event is not None
    row = result_event["stock_pool"][0]
    assert row["pe_ttm"] is None
    assert row["net_profit_growth"] is None
