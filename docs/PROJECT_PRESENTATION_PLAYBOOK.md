# AI Quant Research Workspace — 完整面试手册

> 这份版本以当前项目定位为准。旧的“AI 投资推荐/交易平台”说法已经过时。
> 核心定位是：**证据治理的量化研究操作系统**。

## 1. 一句话定位

### 中文

我做的是一个证据治理的量化研究工作台。它把一个研究问题从假设、实验、验证、稳健性审查、前向观察一直带到人工决策；所有金融指标由确定性后端计算，AI 只能解释已有证据，不能生成收益、替代验证或做最终审批。

### English

I built an evidence-governed operating system for quantitative research. It takes a falsifiable question through experiment, validation, robustness review, forward observation, and a human-owned decision. Deterministic backend services own every financial metric; the LLM may explain supplied evidence, but it cannot create performance truth or approve deployment.

## 2. 30 秒版本

量化研究的问题通常不是缺少一张回测图，而是研究问题、数据、实验、验证和最终决策散落在 notebook 和表格里，别人无法判断证据是否完整、结果是否可复现、还有哪些未知风险。

所以我没有继续做一个信号 dashboard，而是把产品重构成一个研究操作系统：

```text
Research → Experiment → Validation → Robustness
→ Paper Observation → Human Decision
```

它最重要的设计不是“加了 AI”，而是建立了权责边界：后端计算事实，规则判断证据状态，AI 解释证据，人做最终决定。

## 3. 90 秒版本

这个项目最初有很多量化功能：技术指标、回测、模型比较、风险评分和新闻情绪。但它的问题是功能彼此割裂，用户进入“研究库”后不知道研究什么、为什么研究、下一步做什么，而且一些未完成模块以占位符出现，会削弱可信度。

我先重新定义产品对象：不是 ticker，也不是交易信号，而是一个可检验的研究命题。然后设计了六阶段生命周期，并给 Trend 和 Factor 两类研究建立不同的 evidence contract。

以 SPY MA20/MA60 趋势研究为例，系统固定假设、参数、交易成本和同资产 Buy & Hold 基准；信号延迟一天避免未来函数；之后做时间顺序样本外验证、参数敏感性、成本敏感性和数据质量检查。结果不是交给 LLM 计算，而是形成不可混淆的 evidence snapshot。

LangGraph Governance Agent 读取研究定义、检索版本化方法论、检查证据缺口、规划白名单工具，并在昂贵或写入操作前等待人工批准。LLM 最多做一次结构化解释。最终 `Promote / Hold / Reject / Archive` 仍由人记录；如果人的决定与确定性建议不同，必须写 override rationale。

我最后还重做了 UI 信息层级和冷启动恢复：将产品压缩为 Question、Evidence、Challenge、Decision 四个面试展示点；后端启动时所有请求共用一个 readiness gate，而不是每张卡片分别报错。

## 4. 为什么做这个项目

### 原始问题

常见量化作品集有四个可信度问题：

1. 从一个漂亮收益曲线开始，没有可证伪的问题。
2. 展示最佳参数，却不展示样本外、成本和失败结果。
3. 让 AI 生成结论，却不区分计算事实和语言解释。
4. UI 暗示可以交易，但没有 broker、OMS、成交和真实账户。

### 产品决策

我的选择不是继续堆功能，而是建立一条审计链：

- 研究问题必须可证伪；
- 协议和成功标准在结果之前定义；
- 策略必须与合理基准在同一时间区间比较；
- 缺失证据必须保持缺失；
- AI 不能成为金融计算器或审批者；
- 最终结果是一条带依据的人工决策记录。

### 明确不做什么

- 不连接券商；
- 不下实盘订单；
- 不做股票推荐；
- 不承诺未来收益；
- 不把历史回测说成实盘；
- 不把 Paper Observation 说成模拟成交；
- 不把 feature importance 说成因果；
- 不把 workflow coverage 说成置信度。

## 5. 产品生命周期

### 1. Research

回答：

- 问题是什么？
- 假设和零假设是什么？
- 为什么可能有效？
- 用什么资产或横截面？
- 基准是什么？
- 什么结果算通过？
- 已知限制是什么？

### 2. Experiment

固定策略协议并运行历史实验。Trend canonical protocol 是：

- SPY；
- MA20/MA60；
- `MA20 > MA60` 时产生 long signal；
- position 使用前一交易日 signal；
- position 为 0/1；
- 每单位仓位变化成本 0.001；
- 同期 SPY Buy & Hold 为主要基准。

### 3. Validation

按固定顺序生成：

1. historical backtest；
2. benchmark comparison；
3. chronological OOS；
4. parameter sensitivity；
5. transaction-cost sensitivity；
6. data quality。

### 4. Robustness

目前主研究流程中真实实现并展示四项：

- parameter sensitivity；
- benchmark comparison；
- transaction cost；
- data quality。

Regime、Monte Carlo、liquidity/capacity 仍是 scope boundary。Canonical trend walk-forward（固定 MA20/MA60，无逐折调参）已作为 Pressure Test 证据实现；Compare Models 自身的 walk-forward 仍是独立 ML 评估路径，不能冒充 canonical trend robustness。

### 5. Paper Observation

这是一个浏览器/工作区中的前向观察日志：

- cadence；
- minimum days；
- exit criteria；
- dated human notes；
- active/completed。

它不生成订单、成交、仓位或 P&L。

### 6. Decision

系统可以给出确定性建议，但最后由人记录：

- Promote：进入下一层受控研究，不是投入资金；
- Hold：证据不完整、冲突或仍不确定；
- Reject：核心验证或 benchmark 失败；
- Archive：生命周期选择，不代表表现一定差。

## 6. 架构怎么讲

```text
Researcher / Reviewer
        ↓
Next.js 15 + React 19
        ↓ typed API
FastAPI modular monolith
        ├─ Research execution
        ├─ Trend validation
        ├─ Factor validation
        ├─ Evaluation aggregation
        ├─ Model comparison
        ├─ Risk review
        └─ Governance Agent
                ├─ deterministic rulebook retrieval
                ├─ approved tool registry
                ├─ evidence snapshot
                └─ optional OpenAI-compatible LLM
        ↓
Yahoo / AkShare
Optional Supabase Postgres
```

### 为什么是 modular monolith

这个项目需要清楚的模块边界，但作品集和当前流量不需要微服务的部署成本。模块化单体能够：

- 保持一个部署单元；
- 让计算、应用编排、适配器和 UI 权责清楚；
- 避免分布式事务、消息一致性和运维复杂度；
- 未来可以按真实瓶颈拆服务，而不是提前拆。

### 各层权责

| 层 | 负责 | 不负责 |
| --- | --- | --- |
| Next.js | 展示、交互、诚实状态、人工输入 | 重新计算权威金融指标 |
| FastAPI application | 编排用例、校验请求、保存结果 | 把业务真相交给 LLM |
| Calculation engines | 回测、指标、benchmark、validation | 自由文本解释 |
| Provider adapters | 获取并标准化数据、记录 provenance | 用 fixture 冒充 provider 成功 |
| Governance Agent | 检查定义、检索规则、规划白名单工具、组织审阅 | 下单、任意联网、发明数字、最终审批 |
| LLM | 解释已提供的证据 | 计算收益、改变 pass/fail、改变建议 |
| Human | 批准工具、记录最终决策和理由 | 静默改写历史证据 |

## 7. 核心趋势策略如何计算

### 信号和收益

设收盘价为 \(P_t\)。

- 日收益：\(r_t = P_t / P_{t-1} - 1\)
- 短均线：过去 20 个收盘价简单平均
- 长均线：过去 60 个收盘价简单平均
- 原始信号：\(s_t = 1(MA20_t > MA60_t)\)
- 实际仓位：\(position_t = s_{t-1}\)
- 换手：\(|position_t-position_{t-1}|\)
- 成本：`turnover × transaction_cost`
- 毛策略收益：`position × daily return`
- 净策略收益：`gross return − cost`

信号延迟一天是最重要的防未来函数措施之一。当天收盘后才能知道当天 MA，所以不能假设同一收盘价已经完成调仓。

## 8. 核心业绩指标：定义、原因和局限

### Total Return

定义：

```text
ending cumulative equity - 1
```

累计净值使用：

```text
Π(1 + daily net return)
```

为什么需要：回答整个区间最终增长多少。

局限：严重依赖区间长度，不能直接比较不同期限；不表达路径风险。

### CAGR

定义：

```text
(1 + total_return)^(1 / years) - 1
years = observation_count / 252
```

为什么需要：把不同长度结果年化，便于比较增长速度。

局限：把波动路径压缩成一个平滑增长率；收益低于或等于 -100% 时无定义。

### Annualized Volatility

定义：

```text
sample_std(daily return, ddof=1) × sqrt(252)
```

为什么需要：衡量日收益波动幅度，并转成年化口径。

局限：不是全部风险；对非正态、尾部和路径风险刻画有限。

### Sharpe Ratio

定义：

```text
mean(daily return - annual_risk_free_rate / 252)
------------------------------------------------ × sqrt(252)
std(daily excess return)
```

当前 canonical 默认 risk-free rate 为 0。

为什么需要：衡量每单位波动获得的超额收益。

局限：

- 对收益分布和样本区间敏感；
- 不能替代 drawdown；
- Sharpe 高不等于未来可复制；
- 不应跨不同计算口径比较。

### Maximum Drawdown

定义：

```text
min(cumulative_equity / running_peak - 1)
```

为什么需要：表达从历史高点到低点最严重的路径损失。

局限：只描述一个最坏历史路径，不代表未来极端风险。

### Trade Count

canonical 定义：`turnover > 0` 的交易日数量，进入和退出都算一次。

为什么需要：衡量策略动作频率和执行复杂度。

局限：不是完整 round trip 数量，也不是订单笔数。

### Win Rate

canonical 定义：

```text
在 position != 0 的交易日中，net_strategy_return > 0 的比例
```

为什么需要：描述持仓日正收益频率。

局限：

- 不是交易胜率；
- 高胜率可能配合少数大亏；
- 必须结合平均盈亏、收益和 drawdown。

### Turnover

Trend 定义：

```text
Σ |position_t - position_(t-1)|
```

0/1 策略中，一次进入为 1，一次退出为 1。

为什么需要：连接信号频率、交易成本和可执行性。

局限：这是仓位变化单位，不是成交金额或双边成交笔数。

### Total Transaction Costs

定义：

```text
Σ(turnover_t × cost_rate)
```

为什么需要：防止高频切换制造虚假历史优势。

局限：单位是逐期收益扣减的总和，不是美元成本；由于复利，零成本与扣费后 total return 的差不一定等于该总和。

### Exposure Percentage

定义：

```text
mean(abs(position))
```

0/1 策略下就是有仓位的时间比例。

为什么需要：解释为什么策略可能在长期上涨市场落后，也用于判断风险暴露。

局限：不表达仓位内的风险大小，也不等于资金利用效率。

### Downside Capture

定义：

```text
Σ strategy returns on benchmark-negative days
------------------------------------------------
Σ benchmark returns on benchmark-negative days
```

Buy & Hold reference 为 1。

为什么需要：看市场下跌日策略参与了多少下行。

解读：分母通常为负，较低或非正值通常代表较少参与下跌，但必须结合收益和暴露看，不能单独当作质量分数。

### Observation Count

定义：有效 return rows 数量，不是原始下载行数。

为什么需要：给年化指标、OOS 和阈值提供样本背景。

局限：行数多不等于独立信息多，金融时序存在自相关和 regime。

## 9. Benchmark 指标

主要基准使用同资产 Buy & Hold，因为它与策略共享：

- 同一资产；
- 同一数据；
- 同一起止区间；
- 同一有效 observation rows。

这样差异更接近“规则本身的影响”，而不是资产选择的差异。

### Excess Return

```text
strategy total return - benchmark total return
```

### Excess CAGR

```text
strategy CAGR - benchmark CAGR
```

### Sharpe Difference

```text
strategy Sharpe - benchmark Sharpe
```

### Drawdown Improvement

```text
strategy max drawdown - benchmark max drawdown
```

因为 drawdown 是负数，结果为正表示策略回撤较轻。

### Volatility Difference

```text
strategy annualized vol - benchmark annualized vol
```

负值表示策略波动更低。

### OOS Sharpe Difference

```text
OOS strategy Sharpe - OOS benchmark Sharpe
```

这是判断样本外风险调整后是否优于基准的核心检查。

### Benchmark verdict

状态：

- `pass`
- `partial`
- `fail`
- `inconclusive`
- `unavailable`

规则不是简单多数投票：

- blocking 失败可以直接 fail；
- 样本不足或核心指标缺失为 inconclusive；
- 所有配置的 core checks 通过才 pass；
- 核心结果有好有坏时为 partial。

默认 Trend checks：

| 检查 | 默认阈值 | 类型 |
| --- | ---: | --- |
| 扣费后收益相对 B&H | excess return ≥ 0 | core |
| Sharpe 相对 B&H | difference ≥ 0 | core |
| 回撤改善 | improvement ≥ 0.05 | supporting |
| 成本后仍为正收益 | total return ≥ 0 | core |
| OOS Sharpe 相对基准 | difference ≥ 0 | core |
| 参数网格正 Sharpe 比例 | ratio ≥ 0.5 | core |
| 有效样本数 | observations ≥ 252 | core |
| fatal data issues | count ≤ 0 | blocking |

这些是可配置的研究规则，不是统计显著性证明。

## 10. OOS、参数和成本验证

### Chronological OOS

默认按原始价格行的 70% 位置切分：

```text
split_index = floor(raw_observation_count × 0.7)
```

特点：

- 不 shuffle；
- 不用 OOS 调参数；
- 策略先在完整历史上运行一次；
- 再按 split date 切有效 return rows；
- 首个 OOS 行保留与前一个 IS 行之间的真实仓位、换手和成本；
- OOS 累计净值单独 rebased。

最低 OOS 样本：

```text
max(60, long_window)
```

### Parameter Sensitivity

固定网格：

- short：10、20、30；
- long：50、60、100；
- 只保留 short < long；
- 共 9 个组合。

指标：

- valid combination count；
- profitable combination count；
- positive Sharpe count；
- median Sharpe；
- Sharpe range；
- median maximum drawdown；
- canonical percentile by Sharpe。

`canonical percentile by Sharpe` 定义为有效组合中 Sharpe 小于或等于 canonical Sharpe 的比例。它说明 canonical 参数在局部网格的位置，不代表最优概率。

### Transaction-cost Sensitivity

固定成本网格：

- 0；
- 0.001；
- 0.002；
- 0.005。

指标：

```text
return degradation = zero-cost total return - tested-cost total return
Sharpe degradation = zero-cost Sharpe - tested-cost Sharpe
```

为什么需要：一个历史 edge 如果只在零摩擦世界存在，就不够可信。

### Data Quality

Fatal checks：

- normalized OHLCV 字段完整；
- 日期唯一且升序；
- OHLC 均为有效正数。

Informational / warning checks：

- provider/source/retrieval/request bounds；
- cache freshness；
- zero volume；
- requested 与 actual start 的覆盖差；
- 多工作日近似缺口；
- provider notes。

重要边界：项目没有完整 exchange calendar，因此 weekday continuity 是保守近似，不把普通节假日直接判为数据错误。

## 11. 当前缓存快照的真实研究发现

以下数字是从仓库现有 SPY 缓存重新计算的结果：

- 数据最后日期：2026-07-13；
- 有效策略区间：2018-03-28 至 2026-07-13；
- 有效 return rows：2,083；
- 参数：MA20/MA60；
- 成本：每单位仓位变化 0.001；
- 仅用于解释当前仓库快照，不是未来收益承诺。

### Full-period 结果

| 指标 | MA20/60 | SPY Buy & Hold | 解释 |
| --- | ---: | ---: | --- |
| Total return | 87.93% | 226.15% | 策略显著落后 |
| CAGR | 7.93% | 15.38% | 长期增长速度较低 |
| Volatility | 12.37% | 19.14% | 策略波动低约 6.77pp |
| Sharpe | 0.679 | 0.843 | 风险调整后仍未胜 |
| Max drawdown | -27.11% | -33.72% | 回撤改善约 6.60pp |
| Exposure | 73.12% | 100% | 约 27% 时间在现金 |
| Downside capture | 0.614 | 1.000 | 参与约 61% 的下跌日累计下行 |
| Trade count | 35 | N/A | 进入/退出动作日 |
| Cost sum | 3.50% | 0 | 逐期收益成本扣减总和 |

### OOS 结果

OOS 区间：

- 2023-12-15 至 2026-07-13；
- 643 个有效 observation rows。

| 指标 | MA20/60 OOS | B&H OOS |
| --- | ---: | ---: |
| Total return | 32.33% | 64.17% |
| CAGR | 11.60% | 21.44% |
| Volatility | 11.21% | 15.81% |
| Sharpe | 1.036 | 1.308 |
| Max drawdown | -9.96% | -18.76% |

OOS Sharpe difference 为 -0.272，因此没有证明样本外风险调整后优于 B&H。

### 参数发现

- 9/9 参数组合 total return 为正；
- 9/9 参数组合 Sharpe 为正；
- Sharpe range：0.531–1.014；
- median Sharpe：0.684；
- canonical MA20/60 Sharpe percentile：44.4%。

解读：趋势效果不是只存在于一个孤立参数点，但 canonical 参数并不突出，也不能因为全部为正就声称超过 benchmark。

### 成本发现

| 单次仓位变化成本 | Total return | Sharpe |
| ---: | ---: | ---: |
| 0 | 94.62% | 0.714 |
| 0.001 | 87.93% | 0.679 |
| 0.002 | 81.47% | 0.645 |
| 0.005 | 63.34% | 0.541 |

成本越高，收益和 Sharpe 持续下降，但在该历史区间仍保持正值。

### 最终 verdict

`partial`

通过：

- drawdown improvement；
- cost resilience；
- parameter robustness；
- sample sufficiency；
- data quality integrity。

失败：

- return vs Buy & Hold；
- Sharpe vs Buy & Hold；
- OOS Sharpe vs benchmark。

### 最好的面试结论

我没有发现 MA20/60 能在这个区间创造优于 SPY Buy & Hold 的 alpha。它更像一个防御性过滤器：降低市场暴露、波动和最大回撤，但代价是错过长期 equity drift，因此总收益和 Sharpe 都落后。这个 mixed evidence 正好说明为什么产品需要 `partial / Hold`，而不是把所有研究压成一个“好/坏”分数。

## 12. Factor Research 指标

### Universe

当前 canonical universe 是 10 个美国行业 ETF：

`XLB XLE XLF XLI XLK XLP XLU XLV XLY XLRE`

这是静态 preset，不重构历史指数成分，因此必须披露 survivorship/universe limitation。

### Momentum factor

12-1 月动量：

```text
P_(t-1 month) / P_(t-12 months) - 1
```

跳过最近一个月是为了减少短期反转影响，并遵循常见 momentum definition。

### Low Volatility factor

```text
factor = - rolling_std(daily return, 60 days)
```

乘以 -1 是为了统一方向：Q5 永远代表“更强的期望暴露”，所以更低原始波动对应更高 factor score。

### Forward Return

默认 1 个月：

```text
P_(t+1 month-end) / P_(t month-end) - 1
```

只用于标签/结果，不进入形成时的 factor。

### RankIC

每个月横截面：

```text
Spearman correlation(factor rank, forward-return rank)
```

实现上先分别 rank，再做 Pearson correlation。每期至少 3 个有效点；Q1–Q5 需要至少 5 个名字。

为什么需要：判断 factor 是否能在同一期横截面中把未来收益排序。

局限：相关不等于可交易收益，也不代表因果。

### Mean / Median RankIC

- Mean RankIC：跨期 RankIC 平均；
- Median RankIC：降低极端月份影响的中心位置。

### Positive IC Ratio

```text
count(RankIC > 0) / valid IC periods
```

为什么需要：看方向正确的时间稳定性。

### ICIR

```text
mean RankIC / sample_std(RankIC, ddof=1)
```

为什么需要：把 IC 水平和跨期波动放在一起。

局限：当前没有额外年化；样本少或标准差为零时 unavailable。

### Rolling IC

默认 12 期 trailing mean，必须满 12 期才输出。

为什么需要：查看 factor effectiveness 是否随时间变化。

### Q1–Q5 Portfolio Return

每月按 factor 从低到高排序，分成五组；组内等权。余数从 Q1 开始分配。

### Q5−Q1 Gross

```text
Q5 average forward return - Q1 average forward return
```

### Long-short Turnover

long Q5、short Q1：

```text
0.5 × Σ |current weight - previous weight|
```

首次建仓也会产生 turnover。

### Net Long-short Return

```text
gross Q5-Q1 return - turnover × cost_rate
```

### Q5 Excess Return

```text
Q5 cumulative return - equal-weight universe cumulative return
```

为什么 equal-weight universe：它使用同一横截面，但不施加 factor ranking。

### Quantile Monotonicity

计算 Q1→Q5 四个相邻步骤中，右侧平均收益大于等于左侧的比例：

```text
monotonic steps / 4
```

默认 supporting threshold 为 0.75。

### Subperiod Stability

把 RankIC 时序分成前后两半，取两半 mean RankIC 的较小值；默认要求 ≥ 0。

为什么需要：防止所有效果只来自单一早期或晚期区间。

### Factor 默认成功标准

| 指标 | 默认 |
| --- | ---: |
| mean RankIC | ≥ 0 |
| positive IC ratio | ≥ 0.5 |
| net Q5−Q1 return | ≥ 0 |
| Q5 excess return | ≥ 0 |
| mean turnover | ≤ 2.0 |
| observations | ≥ 24 periods |
| ICIR | ≥ 0，supporting |

## 13. Compare Models 怎么讲

### 研究问题

不是“哪个模型最聪明”，而是：

> 在相同的防泄漏样本外窗口、相同成本和相同回测引擎下，ML 模型是否比简单规则或 Buy & Hold 提供更好的风险收益权衡？

### 支持的范式

分类器：

- Logistic L1/L2/ElasticNet；
- Ridge Classifier；
- SVM RBF；
- Random Forest；
- XGBoost；
- LightGBM。

回归：

- Ridge；
- Lasso；
- ElasticNet；
- 预测 next-day return，再按正负转为 0/1 signal。

时间序列：

- ARIMA，对收益做 expanding one-step forecast，不使用 tabular features。

离线 artifact：

- LSTM；
- CNN；
- RL experimental。

重模型不在请求时训练。线上只读取与 ticker、区间和 OOS 条件兼容的 JSON artifact。

### 防泄漏

- chronological split，不 shuffle；
- 标签为 next-day direction/return；
- 特征只使用当时及之前数据；
- split 边界移除最后一条 train row，因为它的 label 使用首个 test-day close；
- scaler/PCA/feature selection/model 只在 train fit；
- rule baseline 在完整历史预热，再切到同一 OOS 日期；
- 所有结果在共享 OOS 区间比较；
- tuning 只在 train 内用 `TimeSeriesSplit`；
- walk-forward 聚合各折 OOS，而不是训练表现。

### Directional Accuracy

```text
correct next-day up/down predictions / OOS observations
```

为什么需要：衡量分类任务本身。

为什么不能作为主结论：

- 预测对小涨和大跌都只记一次；
- 不含交易成本；
- 不表达仓位和收益幅度；
- 高 accuracy 不保证正收益。

### Preprocessing 指标

PCA：

- per-component explained variance ratio；
- cumulative explained variance。

SelectKBest / L1 select：

- selected features；
- dropped features；
- 选择分数只从 train fit。

### Feature Importance

Native：

- tree 的 `feature_importances_`；
- linear 的 normalized absolute coefficient。

Permutation：

- 在 held-out window 打乱一个特征；
- 看模型评分下降；
- 负值截为 0 后归一化。

SHAP：

- tree-only；
- mean absolute SHAP；
- optional dependency 不存在时必须 unavailable。

Coefficient：

- magnitude 和 signed direction 分开；
- 仅适用于 linear model。

这些都是 association/diagnostic，不是因果。

### Importance Stability

至少两个 walk-forward folds。

每个特征计算：

- mean importance；
- sample std；
- coefficient of variation：`std / mean`；
- mean rank；
- rank std。

高 CV 或排名大幅跳动标为 unstable。排名靠前且稳定才列为 consistently matters。

## 14. 21 个 ML 特征

### Momentum

- `return_5d`
- `return_10d`
- `return_20d`
- `return_120d`

定义：`close / close.shift(window) - 1`。

目的：覆盖短、中、长周期趋势。

### Moving-average gaps

- `close / MA5 - 1`
- `close / MA10 - 1`
- `close / MA20 - 1`
- `MA20 / MA60 - 1`

使用 gap 而不是 raw MA，是为了减少价格尺度问题。

### Volatility regime

- 20-day annualized realized vol；
- 60-day annualized realized vol；
- vol20 / vol60。

目的：捕捉短期风险相对长期风险的变化。

### RSI

- RSI7；
- RSI14；
- RSI21。

定义：

```text
RS = rolling average gains / rolling average losses
RSI = 100 - 100 / (1 + RS)
```

### MACD

- MACD = EMA12 − EMA26；
- signal = EMA9(MACD)。

### Bollinger position

```text
(close - MA20) / (2 × rolling_std_20)
```

表达价格相对 20 日中心的位置。

### Volume

- 5-day volume change；
- normalized OBV z-score over rolling 60。

OBV 以收益方向给 volume 加正负号后累计，再做滚动标准化。

### 52-week position

- `close / rolling_252_max - 1`
- `close / rolling_252_min - 1`

表达距 52 周高点和低点的位置。

### 标签

- `y_next_up = next close > current close`
- `y_next_return = next-day return`

两者都不进入 X。

## 15. Risk Review 指标

Risk Review 是可解释的五档规则引擎，不是 VaR 或机构级 risk model。

总体风险：

```text
max(component risk levels)
```

最高风险优先，避免多个中低风险平均后掩盖一个严重项。

### Drawdown

支持：

- current drawdown：当前净值相对峰值；
- historical maximum drawdown：整个回测最坏值。

历史模式使用更宽阈值，避免把历史 max DD 当作实时 current DD 后所有结果都变成 L5。

### Single Trade Loss

从真实 BUY→SELL close price round trip 计算最后一次亏损比例。没有完成交易时为 unavailable/default low，不编造。

### Consecutive Losses

从最新完成的 round trips 向后统计连续亏损数。

### Volatility Level

```text
recent annualized volatility / baseline annualized volatility
```

大致分档：

- ≤1.10：L1；
- ≤1.25：L2；
- ≤1.45：L3；
- ≤1.70：L4；
- 更高：L5。

### Sharpe Decline

比较 recent Sharpe 与 full-period Sharpe。当前 Risk Review 主 route 如果没有可靠 recent Sharpe 会保持 unavailable，不编造。

### Cost Drag Ratio

```text
total transaction cost / pre-cost cumulative return
```

只在 gross return > 0 时计算。

### Signal Conflict

MA 与 momentum 一致为 L1，不一致为 L3；缺失时不假定冲突。

### 风险档位

| Level | Label | 行动 |
| ---: | --- | --- |
| 1 | Green / 正常 | Normal paper research |
| 2 | Light Yellow / 轻度预警 | Cautious |
| 3 | Yellow / 谨慎 | Hold or reduce only |
| 4 | Orange / 高风险 | No new positions |
| 5 | Red / 停止跟随 | Stop / cooldown |

在当前主产品中应把这些理解为研究风险解释，不是实盘交易指令。

## 16. Market Watch 和技术指标

Market Watch 是辅助筛选面，不是核心研究结论。

### Signal Score

五个规则，每项 20 分：

1. close > MA20；
2. MA20 > MA60；
3. 20-day return > 0；
4. RSI14 在 40–70；
5. annualized vol20 < 45%。

总分标签：

- 80–100：Strong Bullish Watchlist；
- 60–79：Bullish Watchlist；
- 40–59：Neutral；
- 20–39：Bearish Watchlist；
- 0–19：High Risk / Avoid。

必须说这是规则型 watchlist 标签，不是投资建议，也不是预测概率。

### Volume Change

```text
volume / volume_MA20 - 1
```

### Distance to MA

```text
close / MA - 1
```

## 17. News Sentiment 指标

AI Insights 是 current-time qualitative panel，没有 point-in-time 历史新闻，因此不能作为回测特征。

### Lexicon polarity

```text
(positive token hits - negative token hits)
------------------------------------------------
(positive hits + negative hits)
```

没有命中时 polarity = 0。

### Score 1–5

- polarity ≤ -0.60 → 1；
- ≤ -0.20 → 2；
- -0.20 至 <0.20 → 3；
- <0.60 → 4；
- ≥0.60 → 5。

### Stance

- 1–2：not favourable；
- 3：neutral；
- 4–5：favourable。

### Recency weight

```text
weight = 0.5^(age_hours / 48)
```

默认 48 小时半衰期。Overall polarity 是 recency-weighted average；正/中/负文章数量仍是未加权计数。

### FinBERT

可选、显式启用、需要 torch 和 transformers。模型 label 的 confidence magnitude 映射到正负 polarity，再进入相同 1–5 规则。

### LLM agreement

LLM 不看到 classifier score，独立给 shadow stance/score。

```text
stance agreement = matching stance count / comparable count
score agreement = exact matching score count / comparable count
```

用途是评估 LLM 与确定性分类器一致性，不是让 LLM 覆盖 classifier。

## 18. Evaluation、Coverage 和 Readiness

### Evidence Coverage

```text
completed implemented validation stages
--------------------------------------- × 100
implemented validation stage count
```

它只表示已实现证据的完成比例。

它不是：

- AI confidence；
- 策略成功概率；
- 模型质量；
- 稳健性得分。

### Workflow Completion

Governance Agent 检查：

- research question；
- hypothesis；
- null hypothesis；
- benchmark；
- active success criteria；
- experiment；
- validation；
- robustness；
- known limitations；
- decision。

```text
completed count / countable items × 100
```

Factor 的 robustness 可为 not applicable。

`decision_ready` 要求 decision 之前的所有 countable 项均 complete。

### Validation status

- 任一 stage failed → failed；
- 否则任一 incomplete → incomplete；
- 否则 completed。

### Evaluation status

- stored validation 中有 failed → blocked；
- 否则有 incomplete → incomplete；
- 否则 completed。

Evaluation 只读取指定 `validation_run_id` 的已有结果并聚合，不重新下载数据、不重新计算。

## 19. Governance Agent 是什么

它不是聊天机器人外壳，而是受控研究 reviewer。

### Graph

```text
classify intent
→ load research context
→ review definition
→ retrieve methodology
→ inspect evidence
→ plan tools
→ wait for approval when required
→ execute registered deterministic tools
→ refresh evidence
→ optional LLM review
→ calculate completeness
→ prepare deterministic suggestion
→ wait for human decision
→ finalize
```

### 支持的 intent

- review definition；
- review readiness；
- review evidence；
- prepare decision。

股票推荐、预测收益、提高杠杆和执行交易请求会被拒绝。

### 白名单工具

Read-only：

- load definition；
- load success criteria；
- load evidence；
- load benchmark；
- load validation/robustness；
- retrieve rulebook；
- load limitations/previous decisions。

Approval-required execution：

- run execution；
- benchmark evaluation；
- OOS；
- parameter sensitivity；
- cost sensitivity；
- data quality；
- factor validation；
- decision readiness。

Approval-required write：

- apply definition draft；
- accept criteria；
- record decision；
- archive research。

### Bounded autonomy

- graph 最多 24 nodes；
- planned tools 最多 8；
- 没有 arbitrary code execution；
- 没有 open web tool；
- interpretation 路径最多一次 model call；
- provider error 不改变确定性证据。

### Rulebook retrieval

当前是版本化本地 Markdown catalog + deterministic lexical ranking，不是向量数据库或互联网论文搜索。

为什么这样选：

- 可审计；
- 可复现；
- 低依赖；
- 每条 methodology citation 有明确版本；
- 当前语料规模不需要 vector DB。

### 双重引用

- Evidence citation：当前 snapshot 中真实计算结果；
- Knowledge citation：方法论规则。

必须分开，因为“这个数字是多少”和“为什么这样解释”是不同证据类型。

## 20. LLM 在哪里体现

LLM 使用 OpenAI-compatible Chat Completions adapter，可配置 OpenAI 或 DeepSeek。

当前部署默认配置指向 DeepSeek；凭据只在后端。

它做：

- research definition review；
- evidence executive summary；
- hypothesis assessment；
- supporting/contradicting evidence 摘要；
- missing evidence 和 next-step explanation；
- news narrative summary；
- shadow sentiment labels。

它不做：

- 回测；
- RankIC；
- Sharpe；
- benchmark verdict；
- completeness；
- deterministic suggestion；
- tool permission；
- human decision。

输出要求：

- low temperature；
- JSON object；
- Pydantic schema validation；
- citation ID filtering；
- unsupported numeric claim safety check；
- 失败时 AI unavailable，确定性工作流继续。

## 21. 确定性建议规则

```text
validation failed 或 benchmark fail
→ Reject

required evidence 缺失 或 decision readiness 不完整
→ Hold

evidence complete 且 benchmark pass
→ Promote

其他 mixed / inconclusive
→ Hold
```

人的决定可以不同，但必须写 override rationale。

这展示了 separation of duties：

- system 提供一致的 policy recommendation；
- AI 提供解释；
- human exercise authority。

## 22. 我做了什么：最强 ownership 版本

### 1. 我重新定义了产品

问题：原项目像多个量化工具的集合，进入研究库后不知道要完成什么。

发现：功能数量不是主要问题，缺的是统一对象和主线。

解决：把主对象从 ticker/signal 改为 research evidence，把结果从“信号”改为 governed decision，建立六阶段 lifecycle 和四站式 guided review。

影响：面试官可以在三分钟内看懂 Question、Evidence、Challenge、Decision。

### 2. 我建立了真实性边界

问题：未计算指标、fake paper state 和未来功能占位符会让作品集看起来更全，但经不起追问。

发现：在金融产品里，诚实的 unavailable 比漂亮的假数字更有价值。

解决：

- backend-only metrics；
- provider failure 不使用 demo fallback；
- no fake P&L/fills/confidence；
- unsupported methods 移到 scope boundary；
- authenticity regression tests。

影响：每个数字都有来源，每个缺口也可见。

### 3. 我为不同研究类型设计不同 evidence contracts

问题：Trend 和 cross-sectional Factor 不能共用同一套 Sharpe checklist。

发现：研究方法不同，正确的评价单位也不同。

解决：

- Trend：same-asset benchmark、OOS、参数、成本、data quality；
- Factor：RankIC、ICIR、quantiles、Q5−Q1、turnover、subperiod stability。

影响：系统不再把不同研究压成一个模糊“score”。

### 4. 我把数据泄漏作为一等风险

问题：随机切分、同日执行、全数据 fit scaler 会让金融 ML 结果虚高。

发现：日频单资产 70% accuracy 往往比 53% 更可疑。

解决：

- chronological split；
- one-row embargo；
- train-only preprocessing/tuning；
- one-day position lag；
- shared OOS window；
- random-walk leakage tests；
- walk-forward。

影响：模型结果可能不漂亮，但可信、可解释、可复现。

### 5. 我没有神化 ML

问题：SPY 有长期正 drift，择时模型容易错过上涨并支付成本。

发现：历史实验中 ML 的 next-day accuracy 大约在低 50% 区间，未稳定击败 Buy & Hold；canonical MA 也主要改善防御性，而非创造 benchmark-relative alpha。

解决：保留负面结果，用 return、Sharpe、drawdown、turnover、cost 和 accuracy 多维比较，而不是挑一个最好看的数。

影响：项目展示的是研究判断，不是营销结果。

### 6. 我约束了 Agent 和 LLM

问题：自由 Agent 可能选错工具、重复计算、引用不相关 evidence，甚至把语言模型意见变成决策。

发现：Agent 的价值是协调治理，不是扩大模型权限。

解决：

- bounded LangGraph；
- tool registry；
- approval gate；
- typed outputs；
- dual citations；
- one-call interpretation；
- deterministic suggestion；
- human override rationale；
- no chain-of-thought exposure。

影响：AI 能提升 review efficiency，但不改变 quantitative truth。

### 7. 我处理了部署中的真实失败

问题：

- Render 冷启动导致每个页面同时报错；
- GitHub warm-up 只能 best effort；
- LightGBM 缺失让整个 Compare Models 返回 500；
- Stooq 返回 browser verification page；
- provider/network failure 被误解为策略失败。

解决：

- shared readiness promise；
- bounded 180-second warmup 和 retry；
- requests queued and resumed；
- typed error categories；
- LightGBM 加入 runtime requirements；
- Stooq 从可选 UI 移除；
- keep-warm 作为优化而非 correctness；
- 推荐 interview reliability 使用 always-on Starter。

影响：基础设施状态不再伪装成研究结论。

### 8. 我重做了 UI 信息层级

问题：大标题、空白卡片、重复 CTA、灰色 disabled text 和过多模块让页面像 landing page，而不是研究工具。

发现：漂亮不等于清楚，Bento 设计必须服务证据层级。

解决：

- quiet canvas；
- consistent card grid；
- restrained accent；
- readable disabled states；
- current research orientation；
- one primary action；
- lifecycle tabs；
- guided review；
- 删除无意义 readiness/mission/placeholder surfaces。

影响：用户先知道“我在研究什么、证据是什么、下一步是什么”，再看细节。

### 9. 我做了重模型与轻部署分离

问题：PyTorch、CNN、LSTM、RL 在线训练会显著增加 Render 镜像、内存、冷启动和失败概率。

解决：训练放在 dev/offline path，提交带条件和时间戳的 result artifact，生产只读兼容 artifact，不 import torch。

影响：保留研究展示能力，同时控制部署成本。

## 23. 最难问题的 STAR 答法

### A. 产品重构

**Situation**：功能很多，但研究库和当前研究页面让用户迷失。

**Task**：让第一次打开的人在几分钟内理解产品价值。

**Action**：审计全部页面，把对象改成 research evidence，建立六阶段 lifecycle；把 evaluation 折叠进 validation；把未实现模块改为 scope boundary；设计四站 guided review；统一 Bento visual hierarchy。

**Result**：产品从 feature tour 变成一个可以完整讲述的 decision workflow。

### B. 防数据泄漏

**Situation**：模型对比很容易因为随机切分和 preprocessing 泄漏得到虚假高分。

**Task**：建立可辩护的样本外对比。

**Action**：chronological split、embargo、train-only fit、shared OOS、one-day lag、TimeSeriesSplit tuning、walk-forward、random-walk regression tests。

**Result**：结果回到合理的低 50% accuracy 区间，并且未击败 B&H；我保留了这个负面结果。

### C. Agent 治理

**Situation**：如果 Agent 能自由调用工具或让 LLM 决定通过，会破坏研究可信度。

**Task**：获得 AI review 效率，同时不让 AI 获得审批权。

**Action**：LangGraph bounded state machine、tool allow-list、approval、structured output、citation separation、deterministic readiness and suggestion、human override rationale。

**Result**：无 LLM key 时系统仍可完成确定性 review；有 LLM 时只增加解释层。

### D. 冷启动

**Situation**：Render sleep 后，Validation、Research 和 Agent 同时请求，用户看到多个独立错误。

**Task**：把 cold start 从随机故障变成可理解的应用状态。

**Action**：一个共享 health promise、最长 180 秒、单次 45 秒、指数退避、ready TTL、请求排队、自动继续和手动 retry。

**Result**：页面不再同时失败；keep-warm 失效时产品仍能自恢复。对关键面试则建议 Starter，因为 scheduled warm-up 不是 SLA。

## 24. 高频追问

### 为什么不用一个综合分数？

因为综合分数会隐藏权衡。这个研究同时具有低波动、低回撤，但低收益和低 Sharpe。把它压成 72 分没有可解释性。系统保留各项 check 和 `partial` verdict，让人看到冲突。

### 为什么用 Buy & Hold？

它是同资产、同期、同数据的最简单机会成本。对于 SPY 趋势择时，如果不能说明相对 B&H 的收益或风险改善，就不能只展示绝对正收益。

### 为什么不是现金基准？

现金零收益只是 secondary reference。主要问题不是“有没有赚钱”，而是规则相对持续持有同资产增加了什么。

### 为什么 MA20/60？

它简单、可解释、可复现，非常适合验证完整研究链。它不是声称最优参数。参数敏感性会检查局部邻域，避免只展示单点。

### 为什么 OOS 仍然不是最终证明？

单次切分依赖一个边界，也可能碰到特定 regime。更强的是多折 walk-forward、regime review、bootstrap uncertainty 和真正的 forward observation。

### 为什么 Factor 用 RankIC 而不是 Accuracy？

Factor 的问题是横截面排序，不是单资产明天涨跌。RankIC 直接衡量 factor ranking 与 forward-return ranking 的关系。

### 为什么 ICIR 不年化？

当前实现定义为 mean IC / std IC，保持透明。若要年化必须明确频率和乘数，不能悄悄改变口径。

### 为什么 AI 不直接选择 Promote？

审批是治理行为，不是文本生成。LLM 可以解释，但 pass/fail 来自确定性规则，最终权力在人。

### RAG 是什么？

当前是小型、版本化 Research Rulebook 的 lexical retrieval。对 10 个左右的治理文档，确定性检索更简单、更可审计。未来语料扩大后才考虑 embeddings/vector search。

### 如果 LLM 挂了呢？

definition checks、evidence availability、tool planning、validation、completeness 和 deterministic suggestion 仍然工作；AI explanation 显示 unavailable。

### 数据是真的吗？

执行路径读取 Yahoo/AkShare 的真实历史数据，保存 provider provenance；失败时显示 unavailable，不替换为演示数字。但它仍是历史研究数据，不是 point-in-time institutional feed，也不是实盘。

### 为什么不直接接券商？

项目目标是展示研究治理。接券商会引入完全不同的合规、账户、order lifecycle、reconciliation 和风险责任，却不会提高当前研究结论的可信度。

### 当前最大的技术债是什么？

Validation result、Agent run、部分 research/observation/decision state 仍存在 process-local 或 browser-local 路径。Render restart 可能丢失 lineage。下一步应优先做 durable persistence，而不是再加模型。

### 下一步最值得做什么？

优先级：

1. durable research/evidence/agent/decision persistence；
2. immutable evidence snapshots and hashes；
3. canonical trend walk-forward；
4. partial model dependency degradation；
5. point-in-time factor universe and richer robustness；
6. E2E and observability。

## 25. 不要说错的地方

不要说：

- “这是交易平台。”
- “Agent 会自动批准策略。”
- “Coverage 代表 80% confidence。”
- “Win rate 是交易胜率。”
- “Feature importance 证明了价格上涨原因。”
- “Paper Observation 是模拟盘 P&L。”
- “所有 robustness 方法都实现了。”
- “GitHub warm-up 保证 Render 永不休眠。”
- “53% accuracy 表示可以稳定赚钱。”
- “Promote 表示可以投入真实资金。”

应该说：

- “这是 research-only workspace。”
- “AI explains; deterministic services calculate; humans decide。”
- “Coverage is implementation completeness。”
- “Win rate is positive return frequency on invested days。”
- “Importance is diagnostic, not causal。”
- “Observation records human forward notes without fake execution。”
- “Unsupported methods remain explicit scope boundaries。”
- “Keep-warm is best effort; Starter is the reliability option。”

## 26. 3 分钟现场演示

### 0:00–0:30 — Home

“这不是一个告诉你买什么的 dashboard。它解决的是：一个量化结论如何从问题走到可审计的人类决策。”

### 0:30–1:00 — Question

打开 Trend Following：

“问题是 MA20/60 在扣除成本后，是否比同一 SPY Buy & Hold 有更好的风险收益表现。参数、基准和成功标准先固定。”

### 1:00–1:40 — Evidence

“信号延迟一天，所有指标来自 FastAPI。这里不仅看 total return，还看 Sharpe、drawdown、exposure 和 downside capture。”

### 1:40–2:20 — Challenge

“系统继续做 chronological OOS、九格参数敏感性、四档成本和 data quality。当前结果是 mixed：回撤更小，但收益和 Sharpe 没赢 B&H。”

### 2:20–3:00 — Decision / Agent

“Agent 可以读取 snapshot、检索方法论、建议工具，但计算和建议规则是确定性的。最终是人记录 Promote、Hold、Reject 或 Archive，并写 rationale。”

收尾：

> Research First. Evidence Before Interpretation. Humans Own Decisions.

## 27. 8 分钟展示顺序

| 分钟 | 页面 | 核心内容 |
| ---: | --- | --- |
| 0–1 | Research Home | 问题、定位、非目标 |
| 1–2 | Definition | 假设、零假设、协议、成功标准 |
| 2–3 | Experiment | one-day lag、成本、指标 |
| 3–4 | Validation | OOS、benchmark、lineage |
| 4–5 | Robustness | 参数、成本、data quality、scope boundary |
| 5–6 | Factor/Models | 不同 evidence contract、防泄漏 |
| 6–7 | Agent | graph、tool approval、LLM boundary |
| 7–8 | Decision | mixed result、人类理由、下一步 |

## 28. 一分钟“我的 initiative”

我最大的 initiative 不是多加了一个 Agent，而是重新定义了产品的信任模型。原来它是很多量化功能的集合，我把它变成一条从可证伪问题到人工决策的研究链。然后我把这个决定贯穿到架构：后端拥有指标，规则拥有验证状态，AI 只能解释，工具调用要审批，最终决策归人。与此同时，我把失败和未知做成一等状态，处理了数据泄漏、provider failure、冷启动、可选依赖和 UI 信息层级。最终项目展示的不是一个被调到最好看的策略，而是一套可以被挑战、复现和治理的工作方法。

## 29. 一分钟收尾

这个项目让我最重要的发现是，量化产品的可信度不来自模型数量，而来自证据边界。一个策略可以降低回撤但仍然不值得 Promote；一个模型可以有 53% 方向准确率但不产生更好的净收益；一个 LLM 可以写出很流畅的解释但没有资格改变验证结果。

所以我最终交付的不只是 Next.js、FastAPI、模型和 Agent，而是一套研究控制系统：真实数据、可复现计算、防泄漏验证、显式未知、受控 AI 和人工责任。我认为这种工程与产品判断，比一条漂亮但无法解释的收益曲线更有价值。

## 30. 面试前检查清单

- 确认 live site 可以打开；
- 确认 backend `/health`；
- 确认最新 deployment；
- 确认 canonical SPY execution；
- 记住结果可能随最新日期变化；
- 记住 cached snapshot 截止 2026-07-13；
- 不把缓存结果说成实时；
- 准备 frontend-safe walkthrough；
- 不依赖 LLM 一定可用；
- 先讲产品问题，再讲技术；
- 先讲 mixed evidence，再讲漂亮 UI；
- 把下一步明确为 persistence + deeper robustness。
