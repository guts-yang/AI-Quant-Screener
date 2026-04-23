from __future__ import annotations

import json
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
                "message": "Data Agent 正在拉取数据...",
                "think": "",
                "timestamp": "2026-01-01T00:00:00",
            }
        )
        event_callback(
            {
                "agent": "CIOAgent",
                "status": "done",
                "message": "CIO Agent 已完成最终研报。",
                "think": "<think>推理链路展示</think>",
                "timestamp": "2026-01-01T00:00:01",
            }
        )

    df = pd.DataFrame(
        [
            {
                "ths_code": "600519.SH",
                "sec_name": "贵州茅台",
                "market_type": "主板",
                "pe_ttm": 23.5,
                "net_profit_growth": 16.2,
                "report_date": "2025-12-31",
            }
        ]
    )
    return {
        "user_query": query,
        "stock_pool": df,
        "risk_assessment": "风险中性偏谨慎。",
        "final_report": "# CIO 研报\n\n建议分批建仓。",
    }


def _build_client(monkeypatch: Any) -> TestClient:
    monkeypatch.setattr(main_module, "init_db", lambda: None)
    return TestClient(main_module.app)


def test_run_endpoint_returns_stock_pool_and_report(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow)
    with _build_client(monkeypatch) as client:
        response = client.post("/api/v1/screener/run", json={"query": "筛选主板股票"})

    assert response.status_code == 200
    payload = response.json()
    assert "stock_pool" in payload
    assert "final_report" in payload
    assert "risk_assessment" in payload
    assert len(payload["stock_pool"]) == 1


def test_stream_endpoint_emits_progress_result_and_done(monkeypatch: Any) -> None:
    monkeypatch.setattr(main_module, "run_agent_workflow", _mock_workflow)
    with _build_client(monkeypatch) as client:
        with client.stream("GET", "/api/v1/screener/stream", params={"query": "筛选主板股票"}) as response:
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
