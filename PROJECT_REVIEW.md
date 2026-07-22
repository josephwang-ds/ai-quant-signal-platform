# 项目 Review（面向求职：DS / AI Engineer / Product Analytics）

## TL;DR
底子很硬（完整、有测试、有部署、"AI 只解释不预测"的诚实定位稀缺），
但有**三块拖后腿**：① 两套后端造成困惑 ② 9 个空壳页面像烂尾 ③ 全项目没有一行真正的机器学习。
把这三点解决 + Phase 1 改名，这个项目就能同时打 DS 和 Product 岗。

---

## 1. 在哪个基础上改？→ 只在 `backend/`

你有两套后端：

| | 行数 | 状态 |
|---|---|---|
| `backend/` | **9718** | 真正部署在 Render，5 段研究链路 + DB + 数据源 + LLM 全在 |
| `apps/api/` | 615 | "目标模块化单体"参考，**只实现了 CreateResearch 一个用例 + 内存仓库**，没接 DB、没部署 |

**结论：所有新功能都在 `backend/` 上做。** `apps/api/` 目前是"未完成的重构"，
对面试是负资产（reviewer 会问"为什么两套后端？哪套是真的？"）。二选一：
- **推荐**：删掉 `apps/api/`，把 clean-architecture 的想法写进 `docs/` 当设计说明。
- 或：README 明确标注它是"架构探索，不参与运行"，别让它看起来像半途而废的迁移。

---

## 2. 需要改 URL 吗？→ 基本不用，但要**删**几条

- **Phase 1 改名**：不用改 URL（已定：只改显示名，风险最低）。`/research`、`/comparison` 这些留着没问题。
- **要动的只有"删"**：下面这些空壳路由建议直接删除（不是改名）：

**孤儿占位页（不在导航里，纯占位，删）：**
```
app/return-quality-lens/     components/features/executive/ReturnQualityLens.tsx
app/scenario-shock-test/     components/features/executive/ScenarioShockTestPanel.tsx
app/strategy-health-score/   components/features/executive/StrategyHealthScorePanel.tsx
app/risk-gate-review/        components/features/risk/RiskGateReview.tsx
app/decision-room/           components/features/decision-room/DecisionRoomPanel.tsx
app/decision-ledger/         components/features/executive/DecisionLedgerPanel.tsx
```
**"即将上线"骨架页（可删，或收进一个 Roadmap 说明）：**
```
app/model-lab/     app/ai-agent/     app/research-notes/   （均为 ModuleSkeletonPage 占位）
```
> 注意：`model-lab` / `ai-agent` 概念上 Phase 2 可能会用；可以先删页面、保留 README 里的路线图文字，
> 等真做时再建。留着空壳只会让 demo 显得烂尾。

---

## 3. 哪些"research"真的不行 / 不实用 / 面试没法讲

**直接判死刑（空壳，讲不出东西）：** 上面第 2 节那 9 个。它们命名唬人（"Return Quality Lens"
"Scenario Shock Test"），点进去却是占位文字——reviewer 一点就穿帮，**比没有还糟**。

**过度设计、性价比低（可讲但不划算）：**
- **Validation 与 Evaluation 拆成两段**：区别太"哲学"（一个算、一个只汇总），
  观众和一半面试官分不清。合并成一个"证据/Evidence"标签（见之前的简化 prompt），
  省下的注意力留给真正的亮点。
- **paper-trading / decision-ledger 这类"决策日志"**：是加分项但不是核心卖点，别当主线讲。

**真正能讲、要留要强化的（这些是你的资产）：**
`overview(Dashboard)`、`market-watch(AI Watchlist)`、`strategy-lab(回测)`、
`comparison(Compare Models)`、`robustness(Risk Review)`、`research/[id]`(可持久化的 5 段链路)。

---

## 4. 还有什么具体改进（按优先级）

**P0 · 补上"真 AI/ML"——这是硬伤**
目前全项目的策略都是确定性规则（MA 交叉 / 动量 / RSI / 组合），`requirements.txt` 里
**没有任何 ML 库**。也就是说打 "Data Scientist / AI Engineer" 时，你的"AI"只有
LLM 解释器 + 规则信号——深度面试会露怯。
→ 旗舰模块 **Compare Models**：在已有的 `/api/backtest/compare-strategies` 上，加
XGBoost / LightGBM 两个真模型，和规则策略同台对比 Return/Sharpe/Drawdown/Turnover/Cost。
**必须带防泄漏纪律**（时间序列 split、无未来函数、样本外、成本敏感性）——这套你项目里已有，搬进去。
这一个模块同时喂 DS（真 ML + 评估）和 Product（"哪个模型好、为什么"可解释）。

**P0 · 删两套后端的困惑**（见第 1 节）。

**P1 · 删 9 个空壳**（见第 2/3 节），Overview 只露能跑的模块。

**P1 · 合并 Validation/Evaluation**，术语去学术化（见 `CURSOR_SIMPLIFY_PROMPTS.md` / Phase 1）。

**P2 · 拆巨型组件**：`ResearchWorkspacePage.tsx` 6 万字节、渲染 39 个区块，
是维护和"讲代码质量"的隐患。按 tab 拆成子组件（不改行为）。

**P2 · Investment Memo**：把 Copilot/评估的输出做成一页可导出 PDF 的投资备忘录，
每条结论可溯源到证据——这是 Product/可解释性叙事的收口。

---

## 面试一句话（改造完之后）
"一个 AI 投资智能平台：LLM 把新闻/财报/信号讲成人话，规则与 ML 模型在**防泄漏的真实回测**上
同台对比，每条推荐都可溯源到证据、可导出备忘录——AI 负责解释，不预测价格。"

对应可深挖的技术点：**模型选择与评估、时间序列防泄漏、回测、推荐排序、LLM 集成、可解释性、产品设计。**
