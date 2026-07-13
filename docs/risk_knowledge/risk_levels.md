# 五档风控等级定义 | Five-Level Risk Governance

> **用途**：供 RAG 检索的风控知识条目。本系统为 **模拟试盘（paper trading）** 治理框架，不涉及实盘下单。  
> **Purpose**: Knowledge base for RAG retrieval. Paper trading governance only — not live trading.

---

## 总原则 | Overview

- 风控等级取各分项指标的 **最高档**（max component level）。
- 等级越高，允许的 **模拟动作（paper action）** 越受限。
- **L3 及以上（Yellow / Orange / Red）**：限制或禁止 **新增模拟仓位**。
- **L5（Red）**：进入 **冷却期（cooling period）**，停止模拟跟随直至人工复核。

---

## L1 — Green | 正常

**中文定义**：风险指标处于正常区间，模拟试盘可按规则推进。

### 典型触发条件 | Triggers

- 当前回撤 ≥ -3%（相对峰值）
- 单笔模拟亏损较轻
- 连续亏损 ≤ 1 次
- 波动率接近或低于基线
- 成本拖累比率较低
- 均线与动量信号无冲突

### 允许的 Paper Action | Allowed Actions

- **Normal paper trading**（正常模拟）
- 允许按策略信号执行模拟买入、卖出或调仓（仍受策略规则约束）

---

## L2 — Light Yellow | 轻度预警

**中文定义**：出现轻微风险抬升，需提高关注，但尚未禁止加仓。

### 典型触发条件 | Triggers

- 回撤约 -3% ~ -6%
- 连续亏损 2 次
- 波动率略高于基线（约 1.1x ~ 1.25x）
- 近期夏普略有走弱

### 允许的 Paper Action | Allowed Actions

- **Cautious paper trading**（小心模拟）
- 可继续模拟，但建议缩小仓位变化幅度、提高审阅频率

---

## L3 — Yellow | 谨慎

**中文定义**：风险明显抬升。**从此档开始限制新增模拟仓位。**

### 典型触发条件 | Triggers

- 回撤约 -6% ~ -10%
- 连续亏损达到 3 次（未达 Red 阈值前）
- 均线与动量信号冲突
- 波动率显著高于基线
- 成本拖累进入中等区间

### 允许的 Paper Action | Allowed Actions

- **Hold or reduce only**（仅持有或减仓）
- **禁止新增模拟仓位（no new simulated positions）**
- 可将原始 BUY 信号降级为 HOLD / WATCH

---

## L4 — Orange | 高风险

**中文定义**：组合处于高压状态，治理上应暂停扩张型模拟动作。

### 典型触发条件 | Triggers

- 回撤约 -10% ~ -15%
- 连续亏损 4 次
- 波动率大幅偏离基线
- 近期夏普转弱至接近零或小幅为负

### 允许的 Paper Action | Allowed Actions

- **No new positions**（暂停新增仓位）
- 仅允许持有、减仓或观望
- 建议标记供 **管理层审阅（leadership review）**

---

## L5 — Red | 停止跟随

**中文定义**：触发硬止损或极端风险组合。**进入冷却期（cooling period）。**

### 典型触发条件 | Triggers

- 回撤超过 -15%，或触及组合硬止损（如 -20%）
- 连续亏损 ≥ 5 次
- 波动率极端放大
- 成本拖累过高，策略边际优势被摩擦吞噬

### 允许的 Paper Action | Allowed Actions

- **Stop following / cooldown**（停止模拟跟随）
- **进入 cooling period**（默认冷却约 5 个交易日，可配置）
- 冷却期内 **禁止新开模拟仓**，需人工复核后方可恢复

---

## 等级与动作对照表 | Quick Reference

| Level | Label (EN) | 中文 | 新增模拟仓位 | Paper Action Summary |
|------:|------------|------|:------------:|----------------------|
| L1 | Green | 正常 | 允许 | Normal paper trading |
| L2 | Light Yellow | 轻度预警 | 允许（谨慎） | Cautious paper trading |
| L3 | Yellow | 谨慎 | **限制** | Hold or reduce only |
| L4 | Orange | 高风险 | **禁止** | No new positions |
| L5 | Red | 停止跟随 | **禁止 + 冷却** | Stop following / cooldown |

---

## RAG 检索关键词 | Keywords

`risk level`, `五档风控`, `Green`, `Yellow`, `Orange`, `Red`, `paper action`, `cooling period`, `L3`, `L5`, `新增模拟仓位`, `cooldown`
