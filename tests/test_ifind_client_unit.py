from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from backend.ifind_client import TokenManager, _normalize_codes, _parse_api_payload, fetch_basic_data
from backend.models import ApiTokens, FinancialData


def test_normalize_codes_supports_string_and_list() -> None:
    assert _normalize_codes("600519.SH, 000858.SZ") == ["600519.SH", "000858.SZ"]
    assert _normalize_codes(["600519.SH", " 000858.SZ "]) == ["600519.SH", "000858.SZ"]


def test_parse_api_payload_extracts_indicators() -> None:
    payload: dict[str, Any] = {
        "data": [
            {
                "ths_code": "600519.SH",
                "report_date": "2025-12-31",
                "pe_ttm": 22.6,
                "net_profit_growth": 16.2,
            }
        ]
    }
    rows = _parse_api_payload(payload, ["600519.SH"], ["pe_ttm", "net_profit_growth"])
    assert len(rows) == 2
    assert {row["indicator_name"] for row in rows} == {"pe_ttm", "net_profit_growth"}


def test_fetch_basic_data_uses_cache_when_fresh(db_session: Session, monkeypatch: Any) -> None:
    now = datetime.utcnow()
    db_session.add_all(
        [
            FinancialData(
                ths_code="600519.SH",
                indicator_name="pe_ttm",
                indicator_value=23.5,
                report_date=now - timedelta(days=1),
                update_time=now,
            ),
            FinancialData(
                ths_code="600519.SH",
                indicator_name="net_profit_growth",
                indicator_value=18.2,
                report_date=now - timedelta(days=1),
                update_time=now,
            ),
        ]
    )
    db_session.commit()

    def should_not_call_api(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("requests.post should not be called when cache is fresh")

    monkeypatch.setattr("backend.ifind_client.requests.post", should_not_call_api)
    df = fetch_basic_data("600519.SH", ["pe_ttm", "net_profit_growth"], db=db_session)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "pe_ttm" in df.columns
    assert "net_profit_growth" in df.columns


def test_fetch_basic_data_force_refresh_calls_api_and_persists(db_session: Session, monkeypatch: Any) -> None:
    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "data": [
                    {
                        "ths_code": "600519.SH",
                        "report_date": "2025-12-31",
                        "pe_ttm": 24.8,
                    }
                ]
            }

    monkeypatch.setattr(TokenManager, "get_access_token", lambda self, db=None: "token-from-test")
    monkeypatch.setattr("backend.ifind_client.requests.post", lambda *args, **kwargs: DummyResponse())

    df = fetch_basic_data("600519.SH", ["pe_ttm"], db=db_session, force_refresh=True)
    assert not df.empty
    assert "pe_ttm" in df.columns
    assert float(df.iloc[0]["pe_ttm"]) == 24.8

    persisted = (
        db_session.query(FinancialData)
        .filter(FinancialData.ths_code == "600519.SH", FinancialData.indicator_name == "pe_ttm")
        .all()
    )
    assert persisted


def test_token_manager_refreshes_and_reuses_valid_token(
    db_session: Session,
    seeded_api_token: ApiTokens,
    monkeypatch: Any,
) -> None:
    call_count = {"n": 0}

    class TokenResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            call_count["n"] += 1
            return {
                "data": {
                    "access_token": "new-access-token",
                    "refresh_token": "new-refresh-token",
                    "expires_in": 3600,
                }
            }

    monkeypatch.setattr("backend.ifind_client.requests.post", lambda *args, **kwargs: TokenResponse())

    manager = TokenManager()
    token_1 = manager.get_access_token(db_session)
    token_2 = manager.get_access_token(db_session)

    assert token_1 == "new-access-token"
    assert token_2 == "new-access-token"
    assert call_count["n"] == 1
