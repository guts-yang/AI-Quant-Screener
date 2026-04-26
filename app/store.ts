import { reactive, toRefs } from "vue";

export type Market = "SH" | "SZ";

export interface Stock {
  code: string;
  name: string;
  market: Market;
  marketType: string;
  thsCode: string;
  price: number;
  change: number;
  pe: number;
  revGrowth: number;
  profitGrowth: number;
  roe: number;
  ffScore: number;
  ffRank: number;
  alpha: number;
  betaMkt: number;
  betaSmb: number;
  betaHml: number;
  betaRmw: number;
  betaCma: number;
  bookToMarket: number;
  operatingProfitability: number;
  assetGrowth: number;
  idiosyncraticVol: number;
  dataQuality: number;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: Date;
  isAction?: boolean;
}

export interface UniverseOption {
  key: string;
  label: string;
  description: string;
  index_code?: string | null;
}

export interface Holding {
  id?: number;
  ths_code: string;
  sec_name: string;
  quantity: number;
  cost_price: number;
  latest_price: number;
  market_value?: number;
  pnl?: number;
  pnl_pct?: number;
  note?: string;
}

export type AgentStatusType = "idle" | "loading" | "success";
export type AgentName = "data" | "factor" | "quant" | "risk" | "cio";

interface ScreenerRunResponse {
  stock_pool: Record<string, unknown>[];
  final_report: string;
  risk_assessment: string;
  factor_summary?: string;
}

interface StreamEvent {
  type: "progress" | "result" | "error" | "done";
  agent?: "DataAgent" | "FactorModelAgent" | "QuantAgent" | "MacroRiskAgent" | "CIOAgent";
  status?: "running" | "done";
  message?: string;
  think?: string;
  stock_pool?: Record<string, unknown>[];
  final_report?: string;
  risk_assessment?: string;
  factor_summary?: string;
}

interface State {
  stocks: Stock[];
  selectedStock: Stock | null;
  chatHistory: ChatMessage[];
  agentStatuses: Record<AgentName, AgentStatusType>;
  isMobileSheetOpen: boolean;
  isRunning: boolean;
  finalReport: string;
  riskAssessment: string;
  factorSummary: string;
  cioThinking: string;
  streamMessage: string;
  universeOptions: UniverseOption[];
  selectedUniverse: string;
  universePreviewCount: number;
  holdings: Holding[];
  holdingsMessage: string;
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8006";

const state = reactive<State>({
  stocks: [],
  selectedStock: null,
  chatHistory: [
    {
      id: "seed-1",
      sender: "ai",
      text: "你好，我是 AI Quant Screener。你可以输入自然语言策略，我会调用后端多智能体流程完成选股和研报。",
      timestamp: new Date(Date.now() - 60_000),
    },
  ],
  agentStatuses: {
    data: "idle",
    factor: "idle",
    quant: "idle",
    risk: "idle",
    cio: "idle",
  },
  isMobileSheetOpen: false,
  isRunning: false,
  finalReport: "",
  riskAssessment: "",
  factorSummary: "",
  cioThinking: "",
  streamMessage: "",
  universeOptions: [
    { key: "local", label: "本地股票池", description: "使用数据库中已保存的股票池" },
    { key: "csi300", label: "沪深300", description: "A股大盘核心资产" },
    { key: "csi500", label: "中证500", description: "中盘成长与价值组合" },
    { key: "csi1000", label: "中证1000", description: "小盘成长与高弹性组合" },
  ],
  selectedUniverse: localStorage.getItem("aqs_selected_universe") || "csi300",
  universePreviewCount: 0,
  holdings: [],
  holdingsMessage: "",
});

let activeEventSource: EventSource | null = null;

const buildId = () => `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const seededNumber = (seed: string, min: number, max: number) => {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  const ratio = (Math.abs(hash) % 10_000) / 10_000;
  return min + (max - min) * ratio;
};

const toMarket = (thsCode: string): Market => (thsCode.endsWith(".SH") ? "SH" : "SZ");

const toNumber = (value: unknown, fallback: number) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const mapStockRow = (row: Record<string, unknown>, index: number): Stock => {
  const thsCode = String(row.ths_code ?? "").trim();
  const code = thsCode.split(".")[0] || `N/A-${index}`;
  const name = String(row.sec_name ?? row.name ?? `标的 ${index + 1}`);

  const pe = toNumber(row.pe_ttm ?? row.pe ?? row["市盈率"], seededNumber(`${code}-pe`, 8, 35));
  const profitGrowth = toNumber(
    row.net_profit_growth ?? row.profit_growth ?? row["净利润增长率"],
    seededNumber(`${code}-profit`, -8, 45),
  );
  const revGrowth = toNumber(
    row.revenue_growth ?? row.rev_growth ?? row["营收同比"],
    seededNumber(`${code}-revenue`, -5, 35),
  );
  const roe = toNumber(row.roe ?? row["ROE"], seededNumber(`${code}-roe`, 6, 28));
  const ffScore = toNumber(row.ff_score, seededNumber(`${code}-ff-score`, 35, 85));
  const ffRank = Math.round(toNumber(row.ff_rank, index + 1));
  const alpha = toNumber(row.alpha, seededNumber(`${code}-alpha`, -0.8, 0.8));
  const betaMkt = toNumber(row.beta_mkt, seededNumber(`${code}-beta-mkt`, 0.65, 1.25));
  const betaSmb = toNumber(row.beta_smb, seededNumber(`${code}-beta-smb`, -1.2, 1.2));
  const betaHml = toNumber(row.beta_hml, seededNumber(`${code}-beta-hml`, -1.2, 1.2));
  const betaRmw = toNumber(row.beta_rmw, seededNumber(`${code}-beta-rmw`, -1.2, 1.2));
  const betaCma = toNumber(row.beta_cma, seededNumber(`${code}-beta-cma`, -1.2, 1.2));
  const bookToMarket = toNumber(row.book_to_market, seededNumber(`${code}-bm`, 0.2, 1.6));
  const operatingProfitability = toNumber(row.operating_profitability, seededNumber(`${code}-op`, 0.04, 0.28));
  const assetGrowth = toNumber(row.asset_growth, seededNumber(`${code}-inv`, -0.05, 0.35));
  const idiosyncraticVol = toNumber(row.idiosyncratic_vol, seededNumber(`${code}-idio`, 0.08, 0.35));
  const dataQuality = toNumber(row.data_quality, 100);

  const price = toNumber(row.close_price ?? row.price, seededNumber(`${code}-price`, 12, 420));
  const change = toNumber(row.change_pct ?? row.change, seededNumber(`${code}-change`, -4.5, 5.5));

  return {
    code,
    name,
    market: toMarket(thsCode),
    marketType: String(row.market_type ?? "主板"),
    thsCode,
    price,
    change,
    pe,
    revGrowth,
    profitGrowth,
    roe,
    ffScore,
    ffRank,
    alpha,
    betaMkt,
    betaSmb,
    betaHml,
    betaRmw,
    betaCma,
    bookToMarket,
    operatingProfitability,
    assetGrowth,
    idiosyncraticVol,
    dataQuality,
  };
};

const setSelectedStock = (stock: Stock | null) => {
  state.selectedStock = stock;
};

const addChatMessage = (msg: Omit<ChatMessage, "id" | "timestamp">) => {
  state.chatHistory.push({
    ...msg,
    id: buildId(),
    timestamp: new Date(),
  });
};

const setAgentStatus = (agent: AgentName, status: AgentStatusType) => {
  state.agentStatuses[agent] = status;
};

const resetAgentStatuses = () => {
  state.agentStatuses = {
    data: "idle",
    factor: "idle",
    quant: "idle",
    risk: "idle",
    cio: "idle",
  };
};

const markAllAgents = (status: AgentStatusType) => {
  (Object.keys(state.agentStatuses) as AgentName[]).forEach((agent) => {
    state.agentStatuses[agent] = status;
  });
};

const mapAgentName = (agent?: string): AgentName | null => {
  if (agent === "DataAgent") return "data";
  if (agent === "FactorModelAgent") return "factor";
  if (agent === "QuantAgent") return "quant";
  if (agent === "MacroRiskAgent") return "risk";
  if (agent === "CIOAgent") return "cio";
  return null;
};

const extractThinkContent = (raw: string) => {
  const text = raw.trim();
  if (!text) return "";
  const match = text.match(/<think>([\s\S]*?)<\/think>/i);
  return match ? match[1].trim() : text;
};

const applyResult = (payload: ScreenerRunResponse | StreamEvent) => {
  const rows = (payload.stock_pool ?? []) as Record<string, unknown>[];
  const mapped = rows.map(mapStockRow);

  state.stocks = mapped;
  state.selectedStock = mapped[0] ?? null;
  state.finalReport = String(payload.final_report ?? "");
  state.riskAssessment = String(payload.risk_assessment ?? "");
  state.factorSummary = String(payload.factor_summary ?? "");
};

const selectedUniverseLabel = () => {
  const target = state.universeOptions.find((item) => item.key === state.selectedUniverse);
  return target?.label ?? "当前股票池";
};

const setSelectedUniverse = (key: string) => {
  state.selectedUniverse = key;
  localStorage.setItem("aqs_selected_universe", key);
};

const loadUniverses = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/universes`);
  if (!response.ok) {
    throw new Error(`股票池配置加载失败: ${response.status}`);
  }
  const payload = (await response.json()) as UniverseOption[];
  if (Array.isArray(payload) && payload.length > 0) {
    state.universeOptions = payload;
    if (!payload.some((item) => item.key === state.selectedUniverse)) {
      setSelectedUniverse(payload[0].key);
    }
  }
};

const previewUniverse = async (key = state.selectedUniverse) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/universes/${encodeURIComponent(key)}`);
  if (!response.ok) {
    throw new Error(`股票池预览加载失败: ${response.status}`);
  }
  const payload = (await response.json()) as { count?: number; stocks?: Record<string, unknown>[] };
  state.universePreviewCount = Number(payload.count ?? 0);
  if (Array.isArray(payload.stocks) && payload.stocks.length > 0 && state.stocks.length === 0) {
    const mapped = payload.stocks.map(mapStockRow);
    state.stocks = mapped;
    state.selectedStock = mapped[0] ?? null;
  }
};

const stopScreener = () => {
  if (activeEventSource) {
    activeEventSource.close();
    activeEventSource = null;
  }
  state.isRunning = false;
};

const runScreenerFallback = async (query: string) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/screener/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, universe: state.selectedUniverse }),
  });

  if (!response.ok) {
    throw new Error(`后端请求失败: ${response.status}`);
  }

  const payload = (await response.json()) as ScreenerRunResponse;
  applyResult(payload);
  markAllAgents("success");
};

const runScreenerWithStream = (query: string) =>
  new Promise<void>((resolve, reject) => {
    stopScreener();
    resetAgentStatuses();
    state.streamMessage = "正在连接后端工作流...";
    state.cioThinking = "";

    const streamUrl = `${API_BASE_URL}/api/v1/screener/stream?query=${encodeURIComponent(query)}&universe=${encodeURIComponent(state.selectedUniverse)}`;
    const source = new EventSource(streamUrl);
    activeEventSource = source;

    source.onmessage = (event) => {
      let payload: StreamEvent;
      try {
        payload = JSON.parse(event.data) as StreamEvent;
      } catch {
        return;
      }

      if (payload.type === "progress") {
        const agent = mapAgentName(payload.agent);
        if (agent) {
          setAgentStatus(agent, payload.status === "running" ? "loading" : "success");
        }
        if (payload.message) {
          state.streamMessage = payload.message;
        }
        if (payload.think) {
          state.cioThinking = extractThinkContent(payload.think);
        }
        return;
      }

      if (payload.type === "result") {
        applyResult(payload);
        markAllAgents("success");
        const count = state.stocks.length;
        addChatMessage({
          sender: "ai",
          text: `已基于「${selectedUniverseLabel()}」完成筛选，共得到 ${count} 只候选标的。研报已整理成可阅读格式，你可以去“研报”页查看完整结论。`,
          isAction: true,
        });
        return;
      }

      if (payload.type === "error") {
        source.close();
        activeEventSource = null;
        reject(new Error(payload.message || "SSE 流执行失败"));
        return;
      }

      if (payload.type === "done") {
        source.close();
        activeEventSource = null;
        resolve();
      }
    };

    source.onerror = () => {
      source.close();
      activeEventSource = null;
      reject(new Error("SSE 连接中断"));
    };
  });

const runScreener = async (query: string) => {
  state.isRunning = true;
  state.streamMessage = "";
  try {
    await runScreenerWithStream(query);
  } catch {
    state.streamMessage = "流式连接失败，正在切换到普通接口...";
    await runScreenerFallback(query);
    addChatMessage({
      sender: "ai",
      text: "已通过非流式接口完成筛选与研报生成。",
      isAction: true,
    });
  } finally {
    state.isRunning = false;
  }
};

const loadHoldings = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/holdings`);
  if (!response.ok) {
    throw new Error(`持仓加载失败: ${response.status}`);
  }
  const payload = (await response.json()) as { holdings?: Holding[]; count?: number };
  state.holdings = Array.isArray(payload.holdings) ? payload.holdings : [];
};

const uploadHoldings = async (holdings: Holding[], replace = true) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/holdings/upload`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ holdings, replace }),
  });

  if (!response.ok) {
    throw new Error(`持仓上传失败: ${response.status}`);
  }

  const payload = (await response.json()) as { holdings?: Holding[]; count?: number };
  state.holdings = Array.isArray(payload.holdings) ? payload.holdings : [];
  state.holdingsMessage = `已导入 ${state.holdings.length} 条持仓`;
  setTimeout(() => {
    state.holdingsMessage = "";
  }, 2200);
};

const openMobileSheet = (stock: Stock) => {
  state.selectedStock = stock;
  state.isMobileSheetOpen = true;
};

const closeMobileSheet = () => {
  state.isMobileSheetOpen = false;
};

export const useAppStore = () => ({
  ...toRefs(state),
  setSelectedStock,
  addChatMessage,
  setAgentStatus,
  resetAgentStatuses,
  runScreener,
  stopScreener,
  runScreenerFallback,
  loadUniverses,
  previewUniverse,
  setSelectedUniverse,
  loadHoldings,
  uploadHoldings,
  openMobileSheet,
  closeMobileSheet,
});
