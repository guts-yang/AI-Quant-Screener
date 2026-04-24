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
1. 工作流状态 `State` 包含：`user_query`、`stock_pool`、`factor_summary`、`risk_assessment`、`final_report`
2. 五节点链路：`DataAgent -> FactorModelAgent -> QuantAgent -> MacroRiskAgent -> CIOAgent`
3. `DataAgent`：解析指标并拉取数据
4. `FactorModelAgent`：计算 Fama-French 五因子代理评分与暴露
5. `QuantAgent`：过滤 300/688 并执行因子筛选
6. `MacroRiskAgent`：生成风险评估
7. `CIOAgent`：生成 Markdown 研报

## Phase 4: 后端 API 暴露
状态: 已完成
1. `POST /api/v1/screener/run`：返回选股 JSON + Markdown 报告
2. `GET /api/v1/screener/stream`：SSE 流式返回 Agent 状态与最终结果

## 前端改造（已完成）
1. React/TSX 迁移到 Vue 3
2. 修复前端乱码与语法问题
3. 桌面/移动端布局保持一致

## Phase 5: 联调增强
状态: 已完成
1. 前端 SSE 状态展示增强：实时显示 Agent 状态与 CIO 推理过程（`think`）
2. 后端接口支持流式与非流式两种联调方式
3. 测试用例文件已按项目精简要求移除

## Phase 6: Fama-French 五因子升级
状态: 已完成（代理评分版本）
1. 新增 `FactorModelAgent`，工作流升级为 `DataAgent -> FactorModelAgent -> QuantAgent -> MacroRiskAgent -> CIOAgent`
2. 新增五因子计算模块：综合评分、alpha 代理信号、MKT/SMB/HML/RMW/CMA 暴露、数据质量
3. 新增因子 ORM 表：`factor_characteristics`、`factor_returns`、`factor_exposures`、`factor_scores`、`screening_runs`
4. API 返回新增 `factor_summary` 与股票池五因子字段
5. 前端股票池、Agent 状态、研报 Factors 页完成五因子展示
6. 指标抽取增加白名单与别名映射，避免 LLM mock 文本污染指标缓存
7. FastAPI startup 迁移到 lifespan，UTC 时间处理去除弃用警告

## 下一步迭代建议
1. 接入真实 iFinD 返回字段规范（替换当前兼容解析）
2. 接入完整日频行情与财报公告日，替换当前五因子代理评分为滚动回归版本
3. 新增月度调仓回测模块，验证五因子组合的收益、回撤、换手率和行业暴露
4. 配置真实 DeepSeek Key 并接入更细粒度推理流
5. 为关键服务补充超时重试与指标监控
