from __future__ import annotations

from typing import Any

import pandas as pd

from backend.agent_workflow import AgentWorkflow, LLMResult, run_agent_workflow


def test_quant_agent_filters_300_and_688_boards() -> None:
    workflow = AgentWorkflow()
    sample = pd.DataFrame(
        [
            {"ths_code": "600519.SH", "pe_ttm": 20.0, "net_profit_growth": 10.0},
            {"ths_code": "300750.SZ", "pe_ttm": 18.0, "net_profit_growth": 12.0},
            {"ths_code": "688981.SH", "pe_ttm": 25.0, "net_profit_growth": 20.0},
        ]
    )
    result = workflow._quant_agent(  # noqa: SLF001
        {
            "user_query": "test",
            "stock_pool": sample,
            "risk_assessment": "",
            "final_report": "",
        }
    )
    filtered = result["stock_pool"]
    assert isinstance(filtered, pd.DataFrame)
    assert len(filtered) == 1
    assert filtered.iloc[0]["ths_code"] == "600519.SH"


def test_run_agent_workflow_emits_progress_events(monkeypatch: Any) -> None:
    def fake_load_universe() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"ths_code": "600519.SH", "sec_name": "贵州茅台", "market_type": "主板"},
                {"ths_code": "000858.SZ", "sec_name": "五粮液", "market_type": "主板"},
            ]
        )

    def fake_fetch_basic_data(codes: list[str], indicators: list[str]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {"ths_code": "600519.SH", "pe_ttm": 24.0, "net_profit_growth": 15.0, "roe": 18.0},
                {"ths_code": "000858.SZ", "pe_ttm": 22.0, "net_profit_growth": 12.0, "roe": 16.0},
            ]
        )

    def fake_chat(model: str, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> LLMResult:
        if model == "deepseek-chat" and "提取金融指标字段名" in user_prompt:
            return LLMResult(content='["pe_ttm","net_profit_growth","roe"]')
        if model == "deepseek-reasoner":
            return LLMResult(content="# CIO 研报\n\n结论：测试通过。", think="这里是推理过程")
        return LLMResult(content="市场风险中性，控制仓位。")

    monkeypatch.setattr("backend.agent_workflow._load_universe", fake_load_universe)
    monkeypatch.setattr("backend.agent_workflow.fetch_basic_data", fake_fetch_basic_data)
    monkeypatch.setattr("backend.agent_workflow._deepseek_chat", fake_chat)

    events: list[dict[str, Any]] = []
    result = run_agent_workflow("筛选主板低估值股票", event_callback=events.append)

    assert not result["stock_pool"].empty
    assert result["risk_assessment"]
    assert "CIO" in result["final_report"]
    assert events
    assert {event["agent"] for event in events} == {"DataAgent", "QuantAgent", "MacroRiskAgent", "CIOAgent"}
