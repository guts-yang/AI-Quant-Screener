from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, TypedDict

import pandas as pd
import requests
from sqlalchemy import select

from .database import SessionLocal
from .ifind_client import fetch_basic_data
from .models import StockPool

try:
    from langchain_core.prompts import ChatPromptTemplate

    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False
    ChatPromptTemplate = None  # type: ignore[assignment]

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False
    END = "END"  # fallback sentinel
    StateGraph = None  # type: ignore[assignment]


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_HTTP_TIMEOUT_SECONDS = int(os.getenv("DEEPSEEK_HTTP_TIMEOUT_SECONDS", "60"))


class WorkflowState(TypedDict):
    user_query: str
    stock_pool: pd.DataFrame
    risk_assessment: str
    final_report: str


EventCallback = Callable[[dict[str, Any]], None]


@dataclass
class LLMResult:
    content: str
    think: str = ""


def _emit(callback: EventCallback | None, agent: str, status: str, message: str, think: str = "") -> None:
    if callback is None:
        return
    callback(
        {
            "agent": agent,
            "status": status,
            "message": message,
            "think": think,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


def _deepseek_chat(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
) -> LLMResult:
    if not DEEPSEEK_API_KEY:
        return LLMResult(content="[Mock] 未配置 DEEPSEEK_API_KEY，返回本地模拟结果。")

    url = f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=DEEPSEEK_HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    message = data.get("choices", [{}])[0].get("message", {})
    content = message.get("content", "")
    think = message.get("reasoning_content", "")
    return LLMResult(content=content, think=think)


def _extract_json_list(text: str) -> list[str]:
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    except Exception:
        pass

    # fallback: parse comma-separated
    text = text.replace("\n", ",")
    return [part.strip().strip('"') for part in text.split(",") if part.strip()]


def _render_prompt(system_prompt: str, user_prompt: str) -> tuple[str, str]:
    """Render prompts via LangChain template when available."""
    if not LANGCHAIN_AVAILABLE:
        return system_prompt, user_prompt

    template = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}"),
            ("user", "{user_prompt}"),
        ]
    )
    messages = template.format_messages(system_prompt=system_prompt, user_prompt=user_prompt)
    rendered_system = messages[0].content
    rendered_user = messages[1].content
    return rendered_system, rendered_user


def _load_universe() -> pd.DataFrame:
    with SessionLocal() as db:
        rows = db.execute(select(StockPool)).scalars().all()
    if not rows:
        return pd.DataFrame(columns=["ths_code", "sec_name", "market_type"])

    return pd.DataFrame(
        [{"ths_code": row.ths_code, "sec_name": row.sec_name, "market_type": row.market_type} for row in rows]
    )


def _pick_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {col.lower(): col for col in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def _safe_dataframe_to_markdown(df: pd.DataFrame) -> str:
    """Best-effort table serialization for LLM prompt context.

    Pandas `to_markdown` depends on optional package `tabulate`.
    If unavailable, fallback to a plain-text table so workflow won't fail.
    """
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


class AgentWorkflow:
    def __init__(self) -> None:
        self._event_callback: EventCallback | None = None
        self._graph = self._build_graph() if LANGGRAPH_AVAILABLE else None

    def _build_graph(self):
        workflow = StateGraph(WorkflowState)
        workflow.add_node("DataAgent", self._data_agent)
        workflow.add_node("QuantAgent", self._quant_agent)
        workflow.add_node("MacroRiskAgent", self._macro_risk_agent)
        workflow.add_node("CIOAgent", self._cio_agent)

        workflow.set_entry_point("DataAgent")
        workflow.add_edge("DataAgent", "QuantAgent")
        workflow.add_edge("QuantAgent", "MacroRiskAgent")
        workflow.add_edge("MacroRiskAgent", "CIOAgent")
        workflow.add_edge("CIOAgent", END)
        return workflow.compile()

    def run(self, user_query: str, event_callback: EventCallback | None = None) -> WorkflowState:
        self._event_callback = event_callback
        initial_state: WorkflowState = {
            "user_query": user_query,
            "stock_pool": pd.DataFrame(),
            "risk_assessment": "",
            "final_report": "",
        }

        if self._graph is not None:
            return self._graph.invoke(initial_state)

        # Fallback when langgraph is not installed.
        state = self._data_agent(initial_state)
        state = self._quant_agent({**initial_state, **state})
        state = self._macro_risk_agent({**initial_state, **state})
        state = self._cio_agent({**initial_state, **state})
        return {**initial_state, **state}

    def _data_agent(self, state: WorkflowState) -> dict[str, Any]:
        _emit(self._event_callback, "DataAgent", "running", "Data Agent 正在解析查询条件并拉取数据...")

        query = state["user_query"]
        indicators_prompt = (
            "请从用户选股指令中提取金融指标字段名，返回 JSON 数组。"
            "例如：[\"pe_ttm\",\"net_profit_growth\",\"roe\"]，只输出 JSON。"
        )

        try:
            system_prompt, user_prompt = _render_prompt(
                "你是量化数据助手。",
                f"用户指令: {query}\n{indicators_prompt}",
            )
            llm_result = _deepseek_chat("deepseek-chat", system_prompt, user_prompt)
            indicators = _extract_json_list(llm_result.content)
        except Exception:
            indicators = []

        if not indicators:
            indicators = ["pe_ttm", "net_profit_growth", "roe"]

        universe_df = _load_universe()
        codes = universe_df["ths_code"].tolist() if not universe_df.empty else []
        if not codes:
            _emit(self._event_callback, "DataAgent", "done", "Data Agent 未找到股票池数据，返回空结果。")
            return {"stock_pool": pd.DataFrame()}

        fetched_df = fetch_basic_data(codes, indicators)
        if fetched_df.empty:
            merged = universe_df.copy()
        else:
            merged = universe_df.merge(fetched_df, on="ths_code", how="left")

        _emit(
            self._event_callback,
            "DataAgent",
            "done",
            f"Data Agent 完成数据填充，共 {len(merged)} 条股票记录。",
        )
        return {"stock_pool": merged}

    def _quant_agent(self, state: WorkflowState) -> dict[str, Any]:
        _emit(self._event_callback, "QuantAgent", "running", "Quant Agent 正在执行规则过滤...")

        df = state["stock_pool"]
        if df.empty:
            _emit(self._event_callback, "QuantAgent", "done", "Quant Agent 检测到空股票池。")
            return {"stock_pool": df}

        filtered = df.copy()

        code_prefix = filtered["ths_code"].astype(str).str.split(".").str[0]
        filtered = filtered[~code_prefix.str.startswith(("300", "688"))]

        pe_col = _pick_existing_column(filtered, ["pe_ttm", "pe", "市盈率"])
        npg_col = _pick_existing_column(filtered, ["net_profit_growth", "profit_growth", "净利润增长率"])

        if pe_col:
            filtered = filtered[(pd.to_numeric(filtered[pe_col], errors="coerce") > 0) & (pd.to_numeric(filtered[pe_col], errors="coerce") < 40)]
        if npg_col:
            filtered = filtered[pd.to_numeric(filtered[npg_col], errors="coerce") > 0]

        _emit(
            self._event_callback,
            "QuantAgent",
            "done",
            f"Quant Agent 完成过滤，剩余 {len(filtered)} 条记录。",
        )
        return {"stock_pool": filtered.reset_index(drop=True)}

    def _macro_risk_agent(self, state: WorkflowState) -> dict[str, Any]:
        _emit(self._event_callback, "MacroRiskAgent", "running", "Macro Risk Agent 正在生成市场风险评估...")

        df = state["stock_pool"]
        if df.empty:
            risk = "当前无可用标的，风险评估结果：观望为主，等待新信号。"
            _emit(self._event_callback, "MacroRiskAgent", "done", "Macro Risk Agent 输出了空池风险结论。")
            return {"risk_assessment": risk}

        sample_codes = ", ".join(df["ths_code"].head(8).tolist())
        prompt = (
            "你是宏观风控分析师。"
            f"候选股票: {sample_codes}\n"
            "请给出 4-6 句中文风险评估，包含市场情绪、流动性、行业景气、仓位建议。"
        )
        try:
            system_prompt, user_prompt = _render_prompt("请输出简洁专业结论。", prompt)
            result = _deepseek_chat("deepseek-chat", system_prompt, user_prompt)
            risk = result.content.strip() or "市场风险中性偏谨慎。"
        except Exception:
            risk = "[Mock] 市场风险中性偏谨慎，建议控制单票权重并分批建仓。"

        _emit(self._event_callback, "MacroRiskAgent", "done", "Macro Risk Agent 已生成风险评估。")
        return {"risk_assessment": risk}

    def _cio_agent(self, state: WorkflowState) -> dict[str, Any]:
        _emit(self._event_callback, "CIOAgent", "running", "CIO Agent 正在撰写最终研报...")

        df = state["stock_pool"]
        risk = state["risk_assessment"]

        if df.empty:
            markdown = "# CIO 最终研报\n\n当前未筛选出满足条件的股票，建议继续观察市场与因子信号。"
            _emit(self._event_callback, "CIOAgent", "done", "CIO Agent 已完成空池报告。")
            return {"final_report": markdown}

        table_md = _safe_dataframe_to_markdown(df.head(10))
        prompt = (
            "请基于候选股票和风险评估，输出 Markdown 投研报告。结构包含：\n"
            "1) 执行摘要\n2) 入选标的点评\n3) 风险控制与仓位建议\n4) 结论\n\n"
            f"候选股票表:\n{table_md}\n\n"
            f"风险评估:\n{risk}"
        )

        think = ""
        try:
            system_prompt, user_prompt = _render_prompt("你是首席投资官（CIO）。", prompt)
            result = _deepseek_chat("deepseek-reasoner", system_prompt, user_prompt, temperature=0.3)
            markdown = result.content.strip()
            think = result.think.strip()
        except Exception:
            markdown = (
                "# CIO 最终研报\n\n"
                "## 执行摘要\n"
                "本次策略以估值与盈利增长因子为核心，筛选出具备基本面支撑的主板标的。\n\n"
                "## 风险控制\n"
                f"{risk}\n\n"
                "## 结论\n"
                "建议采用分批建仓、动态止盈止损的执行策略。"
            )

        _emit(
            self._event_callback,
            "CIOAgent",
            "done",
            "CIO Agent 已完成最终研报。",
            think=think,
        )
        return {"final_report": markdown}


_workflow_singleton: AgentWorkflow | None = None


def get_workflow() -> AgentWorkflow:
    global _workflow_singleton
    if _workflow_singleton is None:
        _workflow_singleton = AgentWorkflow()
    return _workflow_singleton


def run_agent_workflow(user_query: str, event_callback: EventCallback | None = None) -> WorkflowState:
    return get_workflow().run(user_query=user_query, event_callback=event_callback)
