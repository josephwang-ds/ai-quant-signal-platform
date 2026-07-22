# Cursor 指令 · 清理空壳 + 把风控引擎接成真「Risk Review」

背景（给 Cursor 的上下文，可放进第一条 prompt 开头）：
- 后端已有一套**真实且带测试**的五档风控引擎：`backend/app/risk/risk_monitor.py`
  （`calculate_overall_risk_level(RiskMonitorInput) -> RiskAssessment.to_dict()`）
  和 `backend/app/risk/risk_profile.py`，测试在 `backend/tests/test_risk_monitor.py`。
  但它**没有接进 `backend/app/main.py`，没有任何路由暴露**——是 dead code。
- 目标：把它接成一个诚实的 Risk Review API + 前端页面；同时删掉 8 个纯占位路由。
- 纪律：**不虚构任何指标**。风控引擎对缺失输入返回等级 1，缺什么就传 None，不要编数。

按顺序执行；每条完成标准为后端 `PYTHONPATH=. pytest -q`、前端 `npx tsc --noEmit && npm test && npm run build` 全绿。

---

## Prompt R-0 —（低风险）删除 8 个空壳路由

```
删除下列**纯占位**的前端路由与其专用组件（它们都是 WorkspacePlaceholder / ModuleSkeletonPage，
零功能，且 decision-room/decision-ledger 的真实功能已由
components/features/research/decision/ResearchDecisionCenter.tsx 在主研究工作台实现）：

要删的路由目录：
  frontend/app/return-quality-lens/
  frontend/app/scenario-shock-test/
  frontend/app/strategy-health-score/
  frontend/app/decision-room/
  frontend/app/decision-ledger/
  frontend/app/model-lab/
  frontend/app/ai-agent/
  frontend/app/research-notes/

要删的专用组件（若无其它引用）：
  frontend/components/features/executive/ReturnQualityLens.tsx
  frontend/components/features/executive/ScenarioShockTestPanel.tsx
  frontend/components/features/executive/StrategyHealthScorePanel.tsx
  frontend/components/features/executive/DecisionLedgerPanel.tsx
  frontend/components/features/decision-room/DecisionRoomPanel.tsx
（保留 components/features/risk/ 目录——risk-gate-review 下一步要用）

清理引用：
1. 从 frontend/lib/workspaceModules.ts 的 WORKSPACE_MODULES 删除 model-lab / ai-agent /
   research-notes 三个条目。
2. 全仓 grep 上述 8 个路由名与被删组件名，删掉所有 import、导航项、测试用例、类型联合成员
   （如某处 section 联合类型里的 "decision-room" 等）。
3. i18n.ts 里仅被这些页面使用的 key（returnQualityLens*、scenarioShockTest*、
   strategyHealthScore*、decisionRoom*、decisionLedger*、modelLab*、aiResearchAgent*、
   researchNotes* 等 placeholder 文案）删掉；被别处复用的 key 保留。
4. 保留 risk-gate-review 路由与 components/features/risk/RiskGateReview.tsx（下一步改造它）。

完成标准：`npx tsc --noEmit && npm test && npm run build` 全绿，无残留 import/断链。
```

---

## Prompt R-1 —（后端）把风控引擎接成 Risk Review 路由

```
在 backend 里新增一个 Risk Review 端点，复用现有风控引擎，风格对齐 main.py 里已有的
POST /api/backtest（run_backtest）：跑一次回测 → 从回测指标映射出风控输入 → 调风控引擎 → 返回评估。

1) 新增 backend/app/api/routes/risk_review.py：
   - APIRouter(prefix="/api/v1/risk", tags=["risk-review"])
   - POST "/review"，请求体复用/参照 app.schemas.BacktestRequest
     （ticker, start_date, end_date?, strategy, short_window, long_window,
      momentum_window, combined_mode, transaction_cost, data_source）。
   - 处理逻辑：
       from app.data_providers.yahoo_provider import load_price_data
       用 run_ma_crossover_backtest / run_combined_signal_backtest 得到 backtest_df
       用 app.backtest.metrics.calculate_backtest_metrics 得到 metrics
       from app.risk.risk_monitor import RiskMonitorInput, calculate_overall_risk_level
   - 指标 → RiskMonitorInput 映射（**只用真实存在的指标；没有的传 None，不要编造**）：
       current_drawdown   = metrics 的最大回撤（负值，例如 max_drawdown / strategy_max_drawdown）
       volatility         = metrics 的年化/区间波动率（若无则 None）
       sharpe_ratio       = metrics 的 sharpe_ratio（若无则 None）
       cost_drag_ratio    = transaction_cost_total / 毛收益（分母<=0 或缺失时传 None）
       consecutive_losses = 从 backtest_df 的 trade_log 里数最近连亏笔数（拿不到就 0）
       last_trade_loss_pct= 最近一笔亏损百分比（拿不到就 None）
       recent_sharpe / ma_signal / momentum_signal = 暂传 None（引擎会安全降级为等级1）
     先打开 calculate_backtest_metrics 的实现确认真实字段名，别猜 key。
   - 返回：{
       "ticker","strategy","start_date","end_date","data_source",
       "metrics": metrics,
       "risk": assessment.to_dict()   # risk_level, risk_label, allowed_action, risk_reasons, component_levels
     }
   - 错误处理照抄 run_backtest：ValueError→404/400，其它→500。

2) 在 backend/app/main.py 注册：
   from app.api.routes.risk_review import router as risk_review_router
   app.include_router(risk_review_router)

3) 新增 backend/tests/test_risk_review.py（离线，用 fixture/monkeypatch 掉 load_price_data，
   参照 tests 里其它离线路由测试的做法）：验证
   - 正常请求返回 200 且含 risk.risk_level ∈ 1..5、risk_label、component_levels 七个分量；
   - 缺失指标时不报错、对应分量为 1；
   - 无价格数据时返回 404。

完成标准：`cd backend && PYTHONPATH=. pytest -q` 全绿。
```

---

## Prompt R-2 —（前端）把 Risk Review 页面从占位换成真实模块

```
把 risk-gate-review 页面从 WorkspacePlaceholder 改造成真实调用后端 /api/v1/risk/review 的模块，
UI 与取数风格对齐现有的 frontend/components/features/comparison/StrategyComparisonPage.tsx
（同样是"填参数 → POST → 渲染结果"），HTTP 用 lib/apiRequest.ts 的 requestJson，
新增函数放 lib/api.ts，仿照其中的 runStrategyComparison。

1) frontend/lib/api.ts 新增：
   export async function runRiskReview(params): Promise<RiskReviewResponse>
   - POST 到 buildApiUrl("api/v1/risk/review")，body 用与 runBacktest 相同的参数结构。
   - 定义 RiskReviewResponse 类型：{ ticker, strategy, ..., metrics, risk: {
       risk_level:number; risk_label:string; allowed_action:string;
       risk_reasons:string[]; component_levels:Record<string,number> } }

2) frontend/components/features/risk/RiskGateReview.tsx 重写为真实组件：
   - 一个简单表单（ticker / 日期 / 策略 / 窗口 / 成本，可复用 comparison 或 backtest 页已有的输入控件）。
   - 提交后调 runRiskReview，渲染：
       · 顶部一张"风险等级"大卡：五档用颜色（1 绿 → 5 红），显示 risk_label + allowed_action。
       · component_levels 七个分量的小网格（drawdown / volatility / sharpe_decline / cost_drag /
         consecutive_losses / single_trade_loss / signal_conflict），每个显示 1–5 等级。
       · risk_reasons 列表（人话解释为什么是这个等级）。
   - loading / error 用 lib/apiRequest 的 getApiDisplayMessage 处理，别自造。
   - 删除对 WorkspacePlaceholder 的依赖。

3) i18n.ts：把 riskGateReview 相关 placeholder 文案换成真实模块文案（en+zh）：
   模块名 "Risk Review /风险评估"、表单标签、七个分量名、五档标签（可直接用后端返回的英文
   risk_label，中文映射用 risk_profile.py 里的 RISK_LABELS_ZH 对应文案）。

4) 把 Risk Review 挂回导航：frontend/lib/workspaceNav.ts 的 tools 组里加一项指向 /risk-gate-review
   （labelKey 复用/新增 navRiskReview → "Risk Review"/"风险评估"）。

完成标准：`npx tsc --noEmit && npm test && npm run build` 全绿；本地 `npm run dev` 打开
/risk-gate-review 能填参数、拿到后端真实五档评估并渲染。
```

---

## Prompt R-3 —（可选 · 收尾）自测与 README 一句话

```
1) 本地起后端 uvicorn app.main:app --port 8000，curl 验证：
   curl -s -X POST http://127.0.0.1:8000/api/v1/risk/review \
     -H 'content-type: application/json' \
     -d '{"ticker":"SPY","start_date":"2022-01-01","strategy":"ma_crossover","short_window":20,"long_window":60,"transaction_cost":0.001}'
   期望返回含 risk.risk_level 与 component_levels。
2) 在 README 的模块列表里，把 Risk Review 从"计划中"改成"已实现：基于回测指标的五档风控评估，
   规则确定性、可解释（component_levels + risk_reasons）"。
3) git diff 复查：确认没有把 backend/app/risk 里的引擎逻辑改动（只新增路由/测试）。
```

---

## 为什么这条值得做（面试点）
- 你把一段**测过但没人调用的 dead code** 变成了端到端功能——本身就是个好故事。
- 可讲：确定性风控分层（七个风险分量 → 取最严档）、可解释性（component_levels + reasons）、
  前后端接线、诚实工程（缺失指标不虚构、安全降级）。
- 和旗舰 Compare Models 并列：一个讲"模型好坏"，一个讲"风险守门"，产品叙事完整。
