from __future__ import annotations

import json
import os

import pytest
from fastapi.testclient import TestClient

from backend.main import app


RUN_LIVE_E2E = os.getenv("RUN_LIVE_E2E", "0") == "1"


@pytest.mark.skipif(not RUN_LIVE_E2E, reason="Set RUN_LIVE_E2E=1 to run live API integration tests")
def test_live_run_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/screener/run",
            json={"query": "筛选低估值且净利润增长为正的主板股票"},
            timeout=180,
        )

    assert response.status_code == 200
    payload = response.json()
    assert "stock_pool" in payload
    assert "final_report" in payload
    assert "risk_assessment" in payload


@pytest.mark.skipif(not RUN_LIVE_E2E, reason="Set RUN_LIVE_E2E=1 to run live API integration tests")
def test_live_stream_endpoint() -> None:
    with TestClient(app) as client:
        with client.stream(
            "GET",
            "/api/v1/screener/stream",
            params={"query": "筛选主板中估值合理且增长稳定的股票"},
            timeout=180,
        ) as response:
            assert response.status_code == 200
            saw_progress = False
            saw_result = False
            saw_done = False

            for line in response.iter_lines():
                if not line:
                    continue
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                if not line.startswith("data: "):
                    continue

                event = json.loads(line[6:])
                etype = event.get("type")
                if etype == "progress":
                    saw_progress = True
                if etype == "result":
                    saw_result = True
                if etype == "done":
                    saw_done = True
                    break

    assert saw_progress
    assert saw_result
    assert saw_done
