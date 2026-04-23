# AI Quant Screener 项目计划

## Phase 1: 基础架构与本地数据库搭建
状态: 已完成
1. FastAPI 后端基础项目结构初始化
2. SQLAlchemy + SQLite 建表：`stock_pool`、`financial_data`、`api_tokens`
3. 初始化脚本 `init_db.py` 可生成 `quant_system.db`

## Phase 2: 同花顺 iFinD API 核心封装
状态: 已完成（含本地降级机制）
1. `TokenManager` 单例实现 Token 读取与自动刷新
2. `fetch_basic_data(codes, indicators)` 请求封装
3. 24 小时 SQLite 缓存拦截，命中缓存直返
4. 统一输出为 Pandas DataFrame

## Phase 3: LangGraph 多智能体工作流
状态: 已完成
1. 工作流状态 `State` 包含：`user_query`、`stock_pool`、`risk_assessment`、`final_report`
2. 四节点链路：`DataAgent -> QuantAgent -> MacroRiskAgent -> CIOAgent`
3. `DataAgent`：解析指标并拉取数据
4. `QuantAgent`：过滤 300/688 并执行基本面因子筛选
5. `MacroRiskAgent`：生成风险评估
6. `CIOAgent`：生成 Markdown 研报

## Phase 4: 后端 API 暴露
状态: 已完成
1. `POST /api/v1/screener/run`：返回选股 JSON + Markdown 报告
2. `GET /api/v1/screener/stream`：SSE 流式返回 Agent 状态与最终结果

## 前端改造（已完成）
1. React/TSX 迁移到 Vue 3
2. 修复前端乱码与语法问题
3. 桌面/移动端布局保持一致

## Phase 5: 测试与联调增强
状态: 已完成
1. 新增后端单元测试（`tests/test_ifind_client_unit.py`、`tests/test_agent_workflow_unit.py`）
2. 新增接口 E2E 测试（`tests/test_api_e2e.py`）
3. 新增可选真实 API Live E2E（`tests/test_api_live_e2e.py`，通过 `RUN_LIVE_E2E=1` 启用）
4. 前端 SSE 状态展示增强：实时显示 Agent 状态与 CIO 推理过程（`think`）

## 下一步迭代建议
1. 接入真实 iFinD 返回字段规范（替换当前兼容解析）
2. 配置真实 DeepSeek Key 并接入更细粒度推理流
3. 将 FastAPI `on_event` 迁移到 lifespan（消除弃用警告）
4. 为关键服务补充超时重试与指标监控
