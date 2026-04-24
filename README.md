# AI Quant Screener

AI Quant Screener 是一个面向 A 股初筛和投研报告生成的本地量化分析原型。项目使用 Vue 3 构建前端交互界面，FastAPI 提供后端 API，并通过多智能体工作流串联数据拉取、Fama-French 五因子代理评分、规则筛选、宏观风险评估和 CIO 研报生成。

> 当前五因子模块是代理评分版本：在完整日频行情和财报公告日数据接入前，系统会基于可用截面指标与确定性 fallback 数据生成稳定的筛选结果，便于本地开发、联调和演示。

## 功能特性

- 自然语言选股：在聊天框输入策略，例如“筛选低估值且净利润增长为正的主板股票”。
- 多智能体流程：`DataAgent -> FactorModelAgent -> QuantAgent -> MacroRiskAgent -> CIOAgent`。
- 五因子代理评分：输出 `ff_score`、`ff_rank`、`alpha`、`beta_mkt`、`beta_smb`、`beta_hml`、`beta_rmw`、`beta_cma` 等字段。
- 数据源与缓存：封装 iFinD 基础数据接口，并使用 SQLite 对财务指标做 24 小时缓存。
- 流式状态展示：后端提供 SSE 接口，前端实时展示 Agent 执行状态和最终结果。
- Markdown 研报：基于候选股票、因子摘要和风险评估生成 CIO 投研报告。
- 本地可运行：未配置 DeepSeek 或 iFinD 时，后端会使用 mock/fallback 逻辑保证流程可跑通。

## 技术栈

- 前端：Vue 3、Vue Router、TypeScript、Vite、Tailwind CSS、lucide-vue-next
- 后端：FastAPI、SQLAlchemy、Pandas、LangGraph、LangChain、Requests
- 数据库：SQLite，默认文件为 `quant_system.db`
- 外部服务：DeepSeek、同花顺 iFinD，可选 Tushare、TickFlow

## 项目结构

```text
.
├── app/                    # Vue 前端源码
│   ├── components/         # 通用组件
│   ├── views/              # Chat、Pool、Report、Profile 页面
│   ├── router.ts           # 前端路由
│   └── store.ts            # 前端状态与 API 调用
├── backend/                # FastAPI 后端源码
│   ├── agent_workflow.py   # 多智能体工作流
│   ├── factor_model.py     # Fama-French 五因子代理评分
│   ├── ifind_client.py     # iFinD Token、接口与缓存封装
│   ├── main.py             # API 入口
│   ├── models.py           # SQLAlchemy ORM 模型
│   └── database.py         # 数据库连接与初始化
├── styles/                 # 前端样式
├── init_db.py              # 初始化数据库和示例股票池
├── requirements.txt        # Python 依赖
├── package.json            # Node 依赖与脚本
└── .env.example            # 环境变量模板
```

## 快速开始

### 1. 克隆并进入项目

```powershell
git clone <your-repo-url>
cd AI-Quant-Screener
```

### 2. 配置环境变量

```powershell
Copy-Item .env.example .env
```

按需编辑 `.env`：

```env
DEEPSEEK_API_KEY=
IFIND_REFRESH_TOKEN=
IFIND_ACCESS_TOKEN=
VITE_API_BASE_URL=http://127.0.0.1:8006
```

如果暂时没有 API Key，也可以保持为空。系统会使用本地模拟结果与确定性 mock 数据完成端到端流程。

### 3. 安装后端依赖

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. 初始化数据库

```powershell
python init_db.py
```

执行后会创建或更新 `quant_system.db`，并在空库中写入一组示例股票池。

### 5. 启动后端

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8006
```

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8006/api/v1/health
```

### 6. 安装并启动前端

另开一个终端：

```powershell
npm install
npm run dev
```

打开 Vite 输出的本地地址，通常是：

```text
http://localhost:5173
```

## API 说明

### 健康检查

```http
GET /api/v1/health
```

返回：

```json
{
  "status": "ok"
}
```

### 数据源配置状态

```http
GET /api/v1/config/data-sources
```

用于检查 iFinD、DeepSeek、Tushare、TickFlow 是否启用和配置。

### 非流式选股

```http
POST /api/v1/screener/run
Content-Type: application/json

{
  "query": "筛选低估值且净利润增长为正的主板股票"
}
```

返回字段：

- `stock_pool`：候选股票池，包含基础指标与五因子字段。
- `factor_summary`：五因子计算摘要。
- `risk_assessment`：宏观风险评估。
- `final_report`：Markdown 格式 CIO 研报。

PowerShell 示例：

```powershell
$body = @{ query = "筛选低估值且净利润增长为正的主板股票" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8006/api/v1/screener/run -Method Post -ContentType "application/json" -Body $body
```

### 流式选股

```http
GET /api/v1/screener/stream?query=<自然语言选股指令>
```

该接口使用 `text/event-stream` 返回进度事件、最终结果和完成事件。前端默认优先使用该接口，连接失败时会自动降级到非流式接口。

## 工作流说明

1. `DataAgent` 解析用户自然语言指令，提取指标字段，并从股票池与 iFinD 缓存中构建数据表。
2. `FactorModelAgent` 计算五因子代理评分、alpha 代理信号、因子暴露和数据质量。
3. `QuantAgent` 执行规则过滤，默认剔除创业板/科创板代码前缀，并过滤估值、增长和因子分数。
4. `MacroRiskAgent` 结合候选标的和因子摘要生成风险评估。
5. `CIOAgent` 汇总股票池、因子结果和风险结论，输出 Markdown 研报。

## 数据库表

主要表包括：

- `stock_pool`：基础股票池。
- `financial_data`：指标数据缓存。
- `api_tokens`：iFinD access token 和 refresh token。
- `factor_characteristics`：因子特征。
- `factor_returns`：因子收益。
- `factor_exposures`：个股因子暴露。
- `factor_scores`：个股因子评分。
- `screening_runs`：筛选任务结果记录。

当前运行链路主要依赖 `stock_pool`、`financial_data` 和 `api_tokens`；其余因子表已建模，方便后续接入真实回测和持久化结果。

## 常用开发命令

```powershell
# 前端开发
npm run dev

# 前端构建
npm run build

# 预览构建产物
npm run preview

# 后端开发
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8006

# 初始化数据库
python init_db.py
```

## 环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `IFIND_BASE_URL` | iFinD API 地址 | `https://quantapi.51ifind.com/api/v1` |
| `IFIND_REFRESH_TOKEN` | iFinD refresh token | 空 |
| `IFIND_ACCESS_TOKEN` | iFinD access token | 空 |
| `IFIND_ACCESS_TOKEN_EXPIRE_SECONDS` | 环境变量 access token 有效秒数 | `3600` |
| `IFIND_HTTP_TIMEOUT_SECONDS` | iFinD 请求超时 | `20` |
| `FINANCIAL_CACHE_TTL_HOURS` | 财务指标缓存时间 | `24` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 空 |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_HTTP_TIMEOUT_SECONDS` | DeepSeek 请求超时 | `60` |
| `ENABLE_TUSHARE` | 是否启用 Tushare 配置展示 | `0` |
| `TUSHARE_TOKEN` | Tushare Token | 空 |
| `ENABLE_TICKFLOW` | 是否启用 TickFlow 配置展示 | `0` |
| `TICKFLOW_API_KEY` | TickFlow API Key | 空 |
| `VITE_API_BASE_URL` | 前端请求后端地址 | `http://127.0.0.1:8006` |
| `DATABASE_URL` | SQLAlchemy 数据库连接串 | `sqlite:///quant_system.db` |

## 注意事项

- 本项目用于量化研究原型和工程演示，不构成投资建议。
- 默认股票池只包含少量示例标的，可通过写入 `stock_pool` 表扩展。
- 当外部数据源不可用时，系统会降级到确定性 mock 数据，因此结果适合验证流程，不适合直接用于真实交易。
- 当前五因子模型尚未接入完整日频收益率面板；后续可将代理评分替换为滚动回归版本。

## 后续迭代方向

- 接入真实 iFinD 返回字段规范，减少兼容解析和 fallback 依赖。
- 接入完整日频行情、财报公告日和复权价格，升级为真实 Fama-French 滚动回归。
- 增加月度调仓回测，评估收益、回撤、换手率、行业暴露和交易成本。
- 将筛选运行结果和研报持久化到 `screening_runs`。
- 为关键服务增加重试、日志指标、异常告警和单元测试。
