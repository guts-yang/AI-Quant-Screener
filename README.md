# AI Quant Screener (Vue)

## 项目说明
本项目已依据 [`Plan.md`](./Plan.md) 完成前端改造：将原 React/TSX 组件重构为 **Vue 3 + Vue Router + Vite + Tailwind CSS v4** 架构，并修复前端核心问题。

## 改造目标（来自 Plan）
1. 技术栈迁移到 Vue
2. 页面组件重写并保持桌面/移动端体验
3. 统一状态管理与交互逻辑
4. 修复已知编码、语法、样式与交互 bug
5. 输出可运行、可维护的工程文档

## 已完成内容
1. 新建 Vue 工程骨架（`vite.config.ts`、`index.html`、`app/main.ts`）
2. 路由改造为 Vue Router（`app/router.ts`）
3. 状态管理改造为组合式 Store（`app/store.ts`）
4. 核心页面迁移为 Vue SFC：
   - `ChatView.vue`
   - `PoolView.vue`
   - `ReportView.vue`
   - `ProfileView.vue`
   - `DashboardView.vue`
5. 核心组件迁移为 Vue SFC：
   - `AgentStatusPill.vue`
   - `MarkdownReport.vue`
   - `MarketBadge.vue`
   - `PriceChangeTag.vue`
   - `MobileBottomSheet.vue`
6. 清理 React 遗留 `.tsx` 文件，统一为 Vue 架构

## Bug 修复
1. 修复多处中文乱码文案
2. 修复标签未闭合与字符串截断导致的语法错误
3. 修复聊天工作流定时器未清理问题（组件卸载时统一回收）
4. 修复 Tailwind 扫描范围，仅支持 `.vue` 时遗漏的问题
5. 修复主题 CSS 中非法字符导致的样式异常

## 目录结构
```text
.
├─ app
│  ├─ App.vue
│  ├─ main.ts
│  ├─ router.ts
│  ├─ store.ts
│  ├─ components
│  │  ├─ AgentStatusPill.vue
│  │  ├─ MarkdownReport.vue
│  │  ├─ MarketBadge.vue
│  │  ├─ MobileBottomSheet.vue
│  │  └─ PriceChangeTag.vue
│  └─ views
│     ├─ ChatView.vue
│     ├─ DashboardView.vue
│     ├─ PoolView.vue
│     ├─ ProfileView.vue
│     └─ ReportView.vue
├─ styles
│  ├─ fonts.css
│  ├─ index.css
│  ├─ tailwind.css
│  └─ theme.css
├─ index.html
├─ package.json
├─ tsconfig.json
├─ vite.config.ts
└─ Plan.md
```

## 本地运行
```bash
npm install
npm run dev
```

## 构建与预览
```bash
npm run build
npm run preview
```

## 验证状态
1. `npm install` 已执行通过
2. `npm run build` 已执行通过

## 下一步建议
1. 接入真实行情与选股 API，替换当前 mock 数据
2. 增加单元测试（store + 组件）和 E2E 测试（移动端交互）
3. 为聊天工作流接入真实 Agent 服务而非本地模拟定时器
