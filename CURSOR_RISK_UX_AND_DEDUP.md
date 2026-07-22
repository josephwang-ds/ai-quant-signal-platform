# Cursor 指令 · Risk Review 增强（可选口径）+ 工作台去重

> 注：`current_drawdown` 已由我直接改成"当前回撤"(修了"永远 L5")。下面在此基础上继续。
> 我理解你说的"截图两块很 confuse" = 工作台顶部 **tab 栏** 和下面的 **"进度"7 步条**
> 显示了同一套生命周期(研究/实验/业绩回顾/风险评估/模拟交易/决策/归档)两遍。
> 若你指的是别的两块，告诉我重定位。

完成标准：后端 `PYTHONPATH=. pytest -q`、前端 `npx tsc --noEmit && npm test -- --run && npm run build` 全绿。

---

## Prompt RR-1 —（后端）修波动率 + 回撤口径可选 + 风险偏好可选

```
目标：让 Risk Review 的评估真正"活"起来，并让用户能选口径。改动集中在
backend/app/api/routes/risk_review.py、backend/app/risk/risk_profile.py、
backend/app/risk/risk_monitor.py（尽量只加不改旧行为）。

A. 修波动率恒为 1 的死档：
   现在 build_risk_monitor_input 传 baseline_volatility=None，导致引擎里 baseline 取自身、
   比值恒为 1、volatility 档永远=1。改成用"近期 vs 全期"对比：
   - volatility = 近端年化波动率（用 backtest_df["daily_return"] 最近 ~60 个交易日的 std × sqrt(252)）
   - baseline_volatility = 全期年化波动率（metrics["volatility"]）
   数据不足时仍传 None（保持诚实、安全降级）。这样"最近是不是比平时更颠"才会体现出来。

B. 回撤口径可选（对应你要的 dropdown）：
   在请求体（继承/扩展 BacktestRequest 或在路由里加参数）加 drawdown_mode: "current" | "historical"，
   默认 "current"：
   - "current"（默认，已实现）：current_drawdown = 最新回撤（strategy_drawdown.iloc[-1]）。
   - "historical"：current_drawdown = metrics["max_drawdown"]（全历史最深），
     且对回撤档使用**重新标定的阈值**（见 C 的 historical profile），避免又回到"永远 L5"。
   返回体里回传 drawdown_mode，让前端知道当前口径。

C. 风险偏好可选（对应你要的 slider/dropdown）：
   在 backend/app/risk/risk_profile.py 增加 CONSERVATIVE_PROFILE / MODERATE_PROFILE
   （与 AGGRESSIVE_PROFILE 同结构，drawdown_levels / single_trade_loss_levels 逐级放宽或收紧），
   并加一个 HISTORICAL_DRAWDOWN_LEVELS=(-0.10,-0.20,-0.35,-0.50) 供 "historical" 口径使用。
   请求体加 risk_profile: "conservative" | "moderate" | "aggressive"（默认 aggressive，保持现状）。
   calculate_overall_risk_level 已接受 profile 参数——路由按所选 profile 传入；
   "historical" 口径时，用带 HISTORICAL_DRAWDOWN_LEVELS 的 profile 变体只改回撤阈值。

D. 测试 backend/tests/test_risk_review.py 增补：
   - current 口径：结束于回撤中的合成数据 → 回撤档随当前回撤变化（不恒为 5）。
   - historical 口径：同一数据用 historical 阈值 → 档位合理、不必然=5。
   - 波动率：构造近端明显放大的序列 → volatility 档 > 1。
   - 三种 risk_profile 各能跑通、component 都在 1..5。

PYTHONPATH=. pytest -q 全绿。
```

## Prompt RR-2 —（前端）Risk Review 加口径与偏好选择器

```
在 frontend/components/features/risk/RiskGateReview.tsx 的表单区加两个控件，
调用 lib/api.ts 的 runRiskReview 时带上：
1. 回撤口径 dropdown：当前状态(current) / 历史最坏(historical)，默认 current。
   旁边一句小字说明区别（当前=现在浮亏多深；历史=这策略最凶时多深）。
2. 风险偏好 —— 用 slider 或 3 档 segmented 控件：保守/中性/进取(conservative/moderate/aggressive)，
   默认进取。
lib/api.ts 的 runRiskReview 参数与 RiskReviewResponse 类型补上 drawdown_mode / risk_profile。
结果区顶部标注当前口径与偏好（"口径：当前状态 · 偏好：进取"），让用户明白这档是怎么来的。
数值/配色沿用 formatters 与现有五档颜色。

npx tsc --noEmit && npm test -- --run && npm run build 全绿。
```

---

## Prompt WS-1 —（前端）工作台去重：生命周期只显示一次

```
问题：Research 工作台顶部有 tab 栏（研究/实验/业绩回顾/风险评估/模拟交易/决策/归档），
下方 Overview 里又有一个 "进度" 7 步条（LifecycleProgress）显示同样这 7 个阶段——重复、confuse。

改法（二选一，默认 A）：
A. 删掉 Overview 里的 LifecycleProgress "进度"块，改由**顶部 tab 栏兼任进度指示**：
   - 在 tab 栏每个 tab 上体现状态：已完成打勾 ✓、当前高亮、未解锁置灰/加锁标（依据现有
     workflow 状态：execution/validation/evaluation 等 ready 与否）。
   - 找到渲染 tab 的组件（ResearchWorkspaceNavigation 或工作台页里 PRIMARY_SECTIONS 的 map），
     给每个 section 传入其完成/当前/锁定状态并加对应样式与 aria。
   - 从 OverviewSection / 工作台 Overview 内容里移除 LifecycleProgress 的渲染与 import
     （组件文件可保留以防他处引用，仅移除此处使用）。
B. 反过来：保留 "进度" 步骤条作为唯一的阶段可视化，把 tab 栏精简为"当前阶段内容切换"，
   不再重复列出全部 7 个阶段名。

采用 A（tab 兼任进度，信息更聚合）。同时确认 "更多" 里的次要项（notebook/timeline/files/settings）
不与主 tab 混在一起，保持主线清爽。

npx tsc --noEmit && npm test -- --run && npm run build 全绿。
```

---

## 顺带（可选）：首页 "MUU / Not configured" 看着像坏了
截图里示例研究显示 "MUU"、"Not configured / 尚未配置" + "草稿"，像未完成。若你也想清：
可以给示例研究一个已配置好的规范名与状态（或在列表里隐藏 "Not configured" 的半成品草稿），
让首页第一眼是"能用的示例"。需要就说，我出一条 prompt。

## 面试角度
- Risk Review 的口径/偏好选择器：体现你懂"风险度量取决于问题定义"（当前 vs 历史、保守 vs 进取），
  比一个写死的分数更有产品与建模判断力。
- 工作台去重：信息架构的克制——"同一件事只呈现一次"，是资深感的细节。
