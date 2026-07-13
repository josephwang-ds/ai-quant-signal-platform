# 决策治理政策 | Decision Governance Policy

> **用途**：供 RAG 检索的系统决策边界说明。适用于 AI Quant Decision Cockpit / 模拟试盘平台。  
> **Scope**: Paper trading and simulated decision support only.

---

## 1. Raw Signal ≠ Paper Action | 原始信号不能直接变成模拟动作

**Policy (EN)**  
A strategy **raw signal** (e.g., BUY, SELL, WAIT) is the output of rule-based logic only. It must **not** be executed directly as a paper trade.

**政策（中文）**  
策略 **原始信号**（如 BUY / SELL / WAIT）仅是规则计算结果，**不能直接**映射为模拟下单或实盘指令。必须经过下游治理流程。

**RAG 关键词**：`raw signal`, `原始信号`, `not execution`, `不能直接下单`

---

## 2. Mandatory Risk Gate Review | 必须经过风控闸口审查

**Policy (EN)**  
Every actionable signal passes through **Risk Gate Review** before a **final paper action** is determined.

**流程（中文）**  
```
Strategy Signal → Risk Gate Review → Final Paper Action
策略信号      → 风控闸口审查    → 最终模拟动作
```

闸口审查输入包括但不限于：
- 当前回撤（drawdown）
- 波动率相对基线
- 连续模拟亏损次数
- 均线与动量信号冲突
- 成本拖累比率
- 近期夏普走弱

**RAG 关键词**：`Risk Gate Review`, `风控闸口`, `gate decision`, `三段式`

---

## 3. Risk Level Overrides Strategy Signal | 风控等级高于策略信号

**Policy (EN)**  
When risk governance level conflicts with the strategy signal, **risk level takes precedence**.

**政策（中文）**  
当策略信号与风控等级冲突时，**以风控等级为准**。例如：
- 策略给出 BUY，但风控为 L3（Yellow）→ 可能降级为 HOLD ONLY，**限制新增模拟仓位**
- 策略给出 BUY，但风控为 L5（Red）→ 进入 **cooling period**，停止模拟跟随

**RAG 关键词**：`risk overrides signal`, `风控优先`, `L3`, `L5`, `cooldown`

---

## 4. AI Explains — Does Not Advise | AI 只能解释，不提供投资建议

**Policy (EN)**  
The **AI Research Agent** may summarize backtests, risk reasons, and ledger entries. It must **not** provide investment advice, price targets, or trade recommendations.

**政策（中文）**  
AI 助手仅用于：
- 解释回测结果、风控原因、台账记录
- 辅助撰写 **研究备注（research notes）**

AI **不得**：
- 给出买入/卖出建议
- 预测价格或保证收益
- 绕过风控闸口直接建议执行模拟交易

**RAG 关键词**：`AI`, `解释`, `not financial advice`, `非投资建议`, `human-in-the-loop`

---

## 5. Simulated Only | 所有输出均为模拟

**Policy (EN)**  
All outputs — metrics, actions, ledger entries, shock scenarios — are **simulated** for research, governance review, and audit trail purposes.

**政策（中文）**  
平台全部输出均为 **模拟（simulated only）**：
- 不连接券商，不下真实单
- 情景冲击测试 **不是市场预测**
- Decision Ledger 是 **审计留痕**，不是交易流水账
- 文案必须包含 simulated / paper trading / 模拟试盘 等边界说明

**RAG 关键词**：`simulated only`, `paper trading`, `模拟试盘`, `not live trading`, `audit trail`

---

## 6. Human-in-the-Loop | 人工复核

**Policy (EN)**  
Critical gate decisions (especially L4/L5 and cooldown release) should record **human notes** in the **Decision Ledger** for accountability.

**政策（中文）**  
关键闸口结论（尤其 L4/L5 及冷却期解除）应在 **决策留痕台账** 中记录 **人工备注（human note）** 与 **后续结果（outcome）**，支撑复盘与问责。

**RAG 关键词**：`human note`, `人工备注`, `Decision Ledger`, `accountability`, `复盘`

---

## 7. 禁止表述清单 | Prohibited Framing

以下内容 **不应** 出现在用户面向文案或 AI 生成结果中：

| 禁止 | 推荐替代 |
|------|----------|
| CFO Risk Dashboard | Return Quality Lens / 收益质量透视 |
| trading bot / 自动交易 | paper trading / 模拟试盘 |
| buy/sell recommendation | simulated action / governance decision |
| guaranteed return / 保证收益 | simulated outcome / 模拟结果 |
| execute order / 实盘下单 | simulated paper action / 模拟动作 |

---

## RAG 检索关键词 | Keywords

`decision policy`, `治理政策`, `Risk Gate`, `simulated only`, `audit trail`, `human-in-the-loop`, `风控优先`, `原始信号`
