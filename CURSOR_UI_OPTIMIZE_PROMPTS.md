# Cursor 指令 · UI 优化（重点：模型对比一眼看懂）

复用已有资产，别造轮子：
- 图表库 **Recharts 2.15**；多序列叠加图模板 `frontend/components/CompareChart.tsx`。
- 主题 `frontend/lib/chartTheme.ts`：`CHART_COMPARE_LINES`（色盲友好多序列配色）、
  `CHART_TOOLTIP_STYLE`、`CHART_GRID_STROKE`、`CHART_TICK_FILL`。
- 格式化 `frontend/lib/formatters.ts`：`formatMetricPercent / formatMetricSharpe /
  formatMetricTrades / getReturnTone / getDrawdownTone`。
- 卡片 `components/ui/MetricSummaryCard.tsx`、空态 `components/ui/EmptyState.tsx`、
  错误文案 `lib/apiRequest.ts` 的 `getApiDisplayMessage`。

> 依赖：本文件的 UI-1 需要 Compare Models 后端先做完（见 `CURSOR_COMPARE_MODELS_PROMPTS.md`），
> 且要先执行下面 **UI-0** 让后端返回净值曲线，否则叠加图没数据。

完成标准：`npx tsc --noEmit && npm test && npm run build` 全绿；后端改动 `PYTHONPATH=. pytest -q` 全绿。

---

## UI-0 —（后端补数据）让 Compare Models 返回净值曲线

```
在 backend/app/models/model_comparison.py 的 run_model_comparison 里，除现有 metrics 外，
额外返回可直接画图的净值曲线（复用 apply_position_and_returns 已算好的 cumulative_strategy）：

- 每个策略/模型在 OOS 窗口的 (date, cumulative_strategy) 序列，起点归一化为 1.0。
- 汇总成 CompareChart 友好的"行式"结构 equity_curve_rows：
    [ {"date":"2023-01-03", "MA Crossover":1.00, "XGBoost":1.00, "Buy & Hold":1.00},
      {"date":"2023-01-04", "MA Crossover":1.01, "XGBoost":1.02, "Buy & Hold":1.00}, ... ]
  key 用各策略的 label；买入持有作为 benchmark 也放进去。
- 只在所有策略共有的 OOS 交易日上对齐（取交集，避免错位）。
- 在返回体加 "equity_curve_rows" 和 "equity_curve_labels": [label...]。

同步更新 backend/tests/test_model_comparison.py：断言 equity_curve_rows 非空、
每行含全部 label、首行各值≈1.0。pytest 全绿。
```

---

## UI-1 —（前端·核心）Compare Models 可视化，让对比一眼看懂

```
在 Compare Models 页面（components/features/comparison/ModelComparisonPage.tsx）结果区，
在表格之上加一组图，顺序如下。用 Recharts，配色一律取 chartTheme。

1) 冠军横幅（一句话结论）：
   读 summary，渲染一行醒目 banner，如
   "OOS 最佳 Sharpe：LightGBM（1.24）｜最高收益：XGBoost｜最低回撤：MA Crossover"。
   下面配 3–4 张 MetricSummaryCard 展示"最佳模型"的 总收益/Sharpe/最大回撤/方向准确率，
   数值用 formatters，收益/回撤用 getReturnTone/getDrawdownTone 上色。

2) 净值曲线叠加图（最直观的"谁赢了"）：
   仿 CompareChart.tsx 写一个多序列 LineChart，data=equity_curve_rows，
   series=equity_curve_labels，颜色取 CHART_COMPARE_LINES。买入持有用灰色虚线基准。
   标题 "样本外净值曲线（起点=1）"，副标题标注 test_start–test_end。

3) 风险–收益散点图（Recharts ScatterChart）：
   x=最大回撤(取绝对值%)，y=总收益(%)，每个策略一个点；
   ML 模型与规则策略用不同颜色/形状区分，冠军点加大加标签；买入持有作参照点。
   直觉：右下方（高收益低回撤）最好。加坐标轴标题与 Tooltip（显示 label+两指标）。

4) 分指标排名条形图（横向 BarChart，3 个小图或一个可切换）：
   分别按 Sharpe / 总收益 / 最大回撤 排序，最优条高亮（emphasis 色），
   让"每个维度谁第一"一目了然。

5) 每个 ML 模型的特征重要性小条形图（用 feature_importance），
   放在表格行展开或图区下方；标题 "模型看重哪些特征"。

6) 视图切换：顶部一个 "图表 / 表格" toggle，默认图表。表格保留（精确数值）。

所有空态/错误用 EmptyState + getApiDisplayMessage；数值格式统一走 formatters。
npx tsc --noEmit && npm test && npm run build 全绿。
```

---

## UI-2 —（前端·全站一致性）把散乱的展示统一起来

```
做一轮低风险的一致性清理，不改业务逻辑：

1) 数字格式统一：全仓搜索手写的 toFixed/百分比拼接（如 (x*100).toFixed(1)+"%"），
   替换为 lib/formatters.ts 的 formatMetricPercent / formatMetricSharpe / formatMetricTrades。
   收益类数值统一用 getReturnTone、回撤类用 getDrawdownTone 上色（正绿负红，色盲友好）。

2) 指标卡统一：各页面自造的"标签+数值"小块，尽量复用 MetricSummaryCard。

3) 三态统一：为主要数据页（Compare Models、Risk Review、Strategy Comparison、Strategy Lab、
   Market Watch）确保都有 loading（骨架或 spinner）、empty（EmptyState）、error
   （getApiDisplayMessage）三态，风格一致。

4) 表格响应式：给所有宽表格套一个可横向滚动的容器（overflow-x:auto 的 wrapper），
   避免窄屏溢出；表头 sticky。

5) 术语/文案沿用 Phase 1 的新命名（AI Watchlist / Strategy Studio / Compare Models /
   Risk Review / Performance Review / Investment Ideas），检查有无漏网的旧词。

npx tsc --noEmit && npm test && npm run build 全绿。
```

---

## UI-3 —（可选·收尾）Dashboard 收口 + 拆巨型组件

```
1) 首页 Dashboard（app/overview 或首页）：做成一个真正的入口仪表盘——
   顶部三张卡直达三个能打的模块（Compare Models / Risk Review / Investment Ideas），
   各配一句话价值点；下面可放最近一次分析的摘要。去掉"模块目录"式的干列表。

2) 拆分 components/features/research/ResearchWorkspacePage.tsx（6 万字节、渲染 ~39 区块）：
   按 tab 抽成子组件（OverviewTab / EvidenceTab / DecisionTab / NotebookTab / SettingsTab），
   父组件只做路由与数据编排。**纯重构、不改行为**，靠现有测试兜底。

npx tsc --noEmit && npm test && npm run build 全绿。
```

---

## 直观对比的效果预期（你可以照着验收）
- 打开 Compare Models：先看到**一句话冠军横幅**，再一张**净值曲线叠加图**看谁走得高、
  一张**风险-收益散点**看谁又稳又赚，一组**排名条形**看各维度第一，
  展开还能看**每个模型看重的特征**。表格留作精确查数。
- 全站数字/颜色/空错态一致，窄屏不溢出。

## 别过度做（避免反效果）
- 不加花哨动画/3D；金融图表要克制、可信。
- 净值曲线只画 OOS 窗口（和指标同区间），不要画训练段，避免"看起来很准"的误导。
- 方向准确率务必标注"非收益承诺"。
