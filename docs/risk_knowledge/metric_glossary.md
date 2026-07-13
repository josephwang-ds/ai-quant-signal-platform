# 指标术语表 | Metric Glossary

> **用途**：供 RAG 检索的指标定义。所有指标默认基于 **模拟数据（simulated）** 与历史回测/试盘上下文。  
> **Disclaimer**：不构成投资建议，不用于实盘交易决策。

---

## Simulated NAV | 模拟净值

**English**: Net asset value of the **paper trading account**, including cash and marked-to-market position value.

**中文解释**：模拟试盘账户的总资产净值，等于现金加持仓市值。用于观察模拟组合规模变化，**不是真实账户余额**。

**典型用途**：Executive Cockpit 快照、情景冲击后的 NAV Impact 展示。

**RAG 关键词**：`simulated NAV`, `模拟净值`, `portfolio value`, `paper account`

---

## YTD Return | 年初至今收益（模拟）

**English**: Year-to-date percentage return of the simulated portfolio from the start of the calendar year.

**中文解释**：从当年年初至当前观察日的模拟组合收益率。属于 **模拟绩效指标**，不代表未来收益。

**注意**：演示数据可能使用固定 mock 值；生产环境应基于实际试盘记录计算。

**RAG 关键词**：`YTD`, `年初至今`, `simulated return`

---

## Max Drawdown | 最大回撤

**English**: Largest peak-to-trough decline in simulated portfolio value over the evaluation window.

**中文解释**：在观察区间内，净值从前期高点回落到后续低点的 **最大跌幅**。衡量最坏情况下的下行风险，是风控分档的核心输入之一。

**风控关联**：回撤越深，五档等级越高（参见 `risk_levels.md`）。

**RAG 关键词**：`max drawdown`, `最大回撤`, `drawdown`, `peak to trough`

---

## Sharpe Ratio | 夏普比率

**English**: Risk-adjusted return measure: mean excess return divided by return volatility (often annualized).

**中文解释**：单位风险所获得的超额收益，衡量 **风险调整后表现**。数值越高通常表示单位波动带来的回报越好，但不保证样本外持续有效。

**风控关联**：近期夏普相对全样本走弱时，可能触发等级上调。

**RAG 关键词**：`Sharpe`, `夏普`, `risk-adjusted`, `风险调整`

---

## Cost Drag | 成本拖累

**English**: Total simulated transaction costs relative to strategy return; friction that erodes paper P&amp;L.

**中文解释**：模拟交易成本（换手、费率）对策略收益的侵蚀。成本拖累过高意味着规则信号可能被摩擦吃掉，需治理审阅是否继续频繁调仓。

**风控关联**：`cost_drag_ratio` 超过阈值时分项等级上升。

**RAG 关键词**：`cost drag`, `成本拖累`, `transaction cost`, `摩擦`

---

## Capital at Risk | 风险敞口

**English**: Estimated capital exposed to adverse price moves in the current simulated position.

**中文解释**：当前模拟持仓在不利价格变动下可能受影响的资金规模。用于 **治理视角** 评估潜在损失敞口，不是保证金或实盘风险限额。

**典型展示**：Return Quality Lens、情景冲击审阅。

**RAG 关键词**：`capital at risk`, `风险敞口`, `exposure`, `敞口`

---

## Drawdown Buffer | 回撤缓冲

**English**: Distance from current drawdown to the next governance threshold (e.g., buffer before Red level).

**中文解释**：当前回撤距离下一档风控阈值（如红色档位）还剩多少空间。缓冲越小，越应限制新增模拟仓位并加强审阅。

**典型展示**：`Drawdown Buffer to Red Level`（距红色档位回撤缓冲）。

**RAG 关键词**：`drawdown buffer`, `回撤缓冲`, `red level`, `阈值`

---

## Strategy Health Score | 策略健康度评分

**English**: Composite simulated score (e.g., 0–100) weighting drawdown, Sharpe drift, cost drag, and risk-governance signals.

**中文解释**：将回撤、夏普漂移、成本拖累、风控信号等加权合成的 **策略健康度评分**，供管理层快速判断策略是否仍适合继续模拟跟随。分数低不代表必须停策略，但应触发复盘。

**注意**：评分为治理辅助指标，**不是投资建议或收益承诺**。

**RAG 关键词**：`health score`, `策略健康度`, `composite score`, `治理`

---

## 指标与模块对照 | Module Mapping

| Metric | 常见展示模块 |
|--------|-------------|
| Simulated NAV | Executive Cockpit |
| YTD Return | Executive Cockpit |
| Max Drawdown | Return Quality Lens, Risk Gate |
| Sharpe Ratio | Return Quality Lens |
| Cost Drag | Return Quality Lens |
| Capital at Risk | Return Quality Lens |
| Drawdown Buffer | Return Quality Lens |
| Strategy Health Score | Executive Cockpit, Strategy Health Score |
