# v2 Phase 1 · 改名/改故事 Cursor 指令（只改显示名，不动路由与后端）

新定位：**AI Investment Intelligence Platform** —— "用 LLM + 推荐 + 量化 + 历史验证，帮用户做更明智的投资决策"。
纪律不变：**LLM 解释，不预测价格；不承诺收益。**

> 范围：只改 i18n 显示文案、导航标签、首页、README。**路由 URL（app/ 文件夹名）保持不变。**
> 每条 prompt 独立可回滚，改完各跑 `npx tsc --noEmit && npm test` 应全绿（可能要同步个别断言了旧文案的测试）。

---

## Prompt P1-A —（低风险）品牌 + 导航 + 模块显示名

```
在 frontend/lib/i18n.ts 里，只改下列 key 的**显示字符串值**（en 与 zh 两个块都改），
不重命名任何 key、不改 TranslationKey 类型、不动路由。

品牌：
- appTitle:       "AI Quant Research Workspace" → "AI Investment Intelligence Platform"
- appTitleShort:  "AI Quant Research"           → "Investment Intelligence"

导航分组与项（en）：
- navGroupTools:  "Research Tools" → "Tools"
- navMarketWatch: "Markets"        → "AI Watchlist"
- navStrategyLab: "Strategy Lab"   → "Strategy Studio"
- navComparison:  "Compare"        → "Compare Models"
- navRobustness:  "Robustness"     → "Risk Review"
- navExperiments: "Saved Runs"     → "Saved Runs"（不变）
- navResearchWorkspace: "Research Library" → "Investment Ideas"

模块标题（en）：
- marketWatch:        "Markets"     → "AI Watchlist"
- strategyLab:        "Backtest"    → "Strategy Studio"
- strategyComparison: "Compare"     → "Compare Models"
- robustnessChecks:   "Robustness"  → "Risk Review"
- modelLab:           "Model Lab"   → "Model Lab"（保留，Phase 2 用）
- overviewTitle:      "Module directory" → "Dashboard"
- researchListTitle:  "Research Library" → "Investment Ideas"

zh 块：把上面每个 key 的中文值改成对应中文——
AI Watchlist=AI 关注列表, Strategy Studio=策略工作室, Compare Models=模型对比,
Risk Review=风险评估, Investment Ideas=投资想法, Dashboard=仪表盘,
Investment Intelligence Platform=AI 投资智能平台, Tools=工具。

改完全仓搜索用户可见文案里残留的 "Quant" / "Research Workspace" / "研究工作台"，
凡是**面向用户展示**的（非注释、非变量名、非路由），按新定位改；技术文档/注释不用动。
最后 `npx tsc --noEmit && npm test` 全绿；若测试断言了旧文案，同步改断言。
```

---

## Prompt P1-B —（低风险）Research 工作台 → "Investment Ideas" 叙事去学术化

```
目标：把 Research 工作台里"学术味"的用户文案，换成投资产品用语，key 不变。
文件：frontend/lib/i18n.ts（en+zh），涉及 research 列表页与工作台的展示串。

替换原则（找到对应 key 改值）：
- "Research question / 研究问题"      → "Objective / 投资目标"
- "Hypothesis / 假设"                 → "Investment thesis / 投资逻辑"
- "Experiment / 实验"（用户可见处）   → "Strategy run / 策略运行"
- "Validation / 验证"（标题）         → "Performance Review / 业绩回顾"
- "Robustness / 稳健性"               → "Risk Review / 风险评估"
- "Evidence / 证据"                   → 保留（"Supporting evidence / 支持证据"）
- landing/列表页里 "quantitative researchers and portfolio reviewers" 这类受众描述
  → 改成 "investors and analysts exploring AI-assisted investment decisions /
    借助 AI 辅助做投资决策的投资者与分析师"

不要改后端返回的字段名、不要改 evaluation_status 之类枚举值，只改**展示文案**。
`npx tsc --noEmit && npm test` 全绿。
```

---

## Prompt P1-C —（低风险）首页重写为产品故事

```
文件：frontend/components/features/research/ResearchListPage.tsx 及其用到的 i18n hero/lede 文案。
目标：首页第一屏讲清楚"这是什么产品"，非量化背景的人也秒懂。

首屏文案改成（en，对应 i18n 的 landing/hero 相关 key，找不到就在 i18n 里新增 key 并在页面引用）：
- 大标题:   "AI Investment Intelligence Platform"
- 副标题:   "Discover opportunities, compare strategies, and get explainable,
             evidence-backed investment insights — powered by LLMs and quantitative analysis."
- 三个价值点（图标+一句话）:
    1. AI Insights — "LLM summarizes news, financials, and signals in plain language."
    2. Compare Models — "Rule-based, momentum, and ML strategies compared on real backtests."
    3. Explainable Memo — "Every recommendation traces to evidence. AI explains, never predicts."
- 一行免责声明保留:  "For research and demonstration. Not investment advice; no live trading."
zh 版同步。

保留现有的 "打开 Trend Following 示例" 入口按钮，只是文案可改为
"Open sample study / 打开示例分析"。不要改数据获取逻辑、不要动后端调用。
`npx tsc --noEmit && npm test` 全绿。
```

---

## Prompt P1-D —（低风险）重写 README 顶部定位

```
重写 README.md 顶部（标题到 "Getting started" 之前的定位/介绍部分），改为 v2 定位：
标题: # AI Investment Intelligence Platform
一句话: "An AI-powered investment intelligence platform that combines LLMs,
recommendation systems, quantitative analysis, and historical validation to help
users make more informed investment decisions."

保留并突出这些卖点（用产品语言，不用学术黑话）：
- AI Insights（LLM 解释新闻/财报/信号）
- AI Watchlist（候选生成 → 排序 → 业务约束 → 可解释 → Top Picks，作为推荐系统能力展示）
- Compare Models（规则/动量/ML 模型在真实回测上对比：Return/Sharpe/Drawdown/Turnover/Cost）
- Performance Review（回测 + 样本外 + 基准对比）
- Risk Review（压力测试/敏感性/市场状态）
- Investment Memo（AI 生成、可导出 PDF、每条结论可溯源）

明确边界那段保留并强调：
✓ AI 用于总结/解释/对比/生成备忘录
✗ AI 不预测明日股价、不承诺收益、不替代投资决策

**不要改** "Getting started / Tech stack / Deployment / Architecture" 这些技术小节的事实内容
（端口、命令、迁移、CORS 等保持准确）；只重写顶部定位叙事。
```

---

## 执行顺序与验收
1. P1-A（品牌/导航/模块名）→ `npm run dev` 看导航和标题。
2. P1-B（工作台去学术化）。
3. P1-C（首页故事）。
4. P1-D（README）。

每条以 `npx tsc --noEmit && npm test` 全绿为完成标准。全部完成后，产品在"听得懂"这层就立住了，
再进 Phase 2 只深耕 **Compare Models + Investment Memo** 一条旗舰线（复用后端已有的
`/api/backtest/compare-strategies`，加真 ML 模型与防泄漏回测）。
