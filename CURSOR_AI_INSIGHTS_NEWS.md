# Cursor 指令 · AI Insights（新闻 → 分类器 → LLM 带引用总结 → 5 档实时面板）

架构原则(贴合你项目护城河)：**确定性分类器给出情感档位(权威)，LLM 只做带引用的可读解释(不预测价格)。**
默认 **Finnhub** 取新闻、**词典分类器**打分(FinBERT 可选)、复用现有 **DeepSeek** 适配器做总结。
**先做"当前实时面板"，不进历史回测**(避免未来函数)。

复用：`app/research_copilot/{openai_adapter, llm_config, system_policy, safety}`(DeepSeek 适配器与"解释不预测"策略)、
`app/config.py`(env 读取)。完成标准：后端 `PYTHONPATH=. pytest -q`、前端 `npx tsc --noEmit && npm test -- --run && npm run build` 全绿。

---

## AIN-1 —（后端·取新闻，供应商可插拔）

```
新建 backend/app/insights/ 包。
1) news_port.py：定义 NewsItem(dataclass: id, headline, summary, url, source, published_at)
   和 NewsProvider Protocol: fetch_recent(ticker, limit) -> list[NewsItem]。
2) finnhub_provider.py：调 Finnhub company-news REST（GET /company-news?symbol=&from=&to=），
   用 stdlib urllib（不加 SDK，参照 openai_adapter 的做法），API key 从 env FINNHUB_API_KEY 读；
   未配置时抛可识别的 NotConfigured。
3) fixture_provider.py：离线测试用的假新闻源（固定几条），供单测注入。
4) config：FINNHUB_API_KEY 走后端 env（render.yaml 加 sync:false；**绝不放 NEXT_PUBLIC_***）。
   provider 选择：有 key 用 Finnhub，否则可回退 yfinance ticker.news（已装 yfinance，零成本、无情感）。
5) 简单缓存：对 (ticker) 结果做 ~10 分钟内存缓存，避免打爆免费额度。
```

## AIN-2 —（后端·分类器，确定性、真 NLP）

```
新建 backend/app/insights/sentiment.py —— 每条新闻打情感档，**这是"分类"步、不交给 LLM**。
默认用金融词典(轻、无重依赖)：
- classify_item(text) -> {stance: "favourable"|"neutral"|"not_favourable", score_1_5: int, polarity: float}
  用 Loughran-McDonald 金融正/负词表(可用 pysentiment2 或内置精简词表)统计正负词，
  归一到 polarity∈[-1,1] → 映射 5 档(1 很不利…5 很有利)。
- aggregate(items) -> {overall_stance, overall_score_1_5, positive/neutral/negative 计数}
  按时间衰减加权(近的权重高)。
(可选，gated) FinBERT：sentiment_finbert.py 用 transformers 金融情感模型，
  torch 只进 requirements-dev、**离线/受开关控制**，不进 Render 运行时默认路径。

测试：给定固定文本，分类结果确定、5 档边界正确、aggregate 计数与加权对。
```

## AIN-3 —（后端·LLM 带引用总结 + 路由）

```
1) insights/summary.py：复用 app/research_copilot 的 DeepSeek 适配器与系统策略，
   输入=已分类的新闻条目(含 stance/score)，产出一段自然语言总结 + 每条要点 + 引用(url/source)。
   **严守 system_policy：基于所给新闻解释、给理由与引用，不预测价格、不承诺收益。**
   LLM 未配置(无 LLM_API_KEY)时优雅降级：返回分类结果 + "summary 不可用(未配置)"。
2) 新建 app/api/routes/insights.py：
   APIRouter(prefix="/api/v1/insights")
   POST "/news-sentiment" body: {ticker, limit?=10, use_finbert?=false, paste_text?}
   流程：取新闻(AIN-1) → 逐条分类(AIN-2) → 聚合 → LLM 总结(可选) → 返回：
   {
     ticker, generated_at,
     overall: {stance, score_1_5, counts},
     items: [{headline, url, source, published_at, stance, score_1_5, reason}],
     summary: {text, disclaimer} | null,
     provider, classifier, notice: "Live snapshot; not a backtest feature; AI interpretation, not advice."
   }
   在 main.py 注册。错误分类同其它路由(未配置→503/友好提示，新闻源失败→502/降级)。
3) render.yaml 加 FINNHUB_API_KEY (sync:false)。

测试(离线，注入 fixture_provider + fake LLM)：
- 正常返回 overall 5 档 + items 带 stance；
- 无 LLM_API_KEY 时 summary=null 但分类仍在；
- 无新闻时优雅空态；不因 LLM 失败而整体 500。
```

## AIN-4 —（前端·AI Insights 面板）

```
新建 AI Insights 页/卡(可挂 /ai-insights 或作为 Dashboard 一块)：
- 输入 ticker(+可选粘贴新闻文本)、可选"用 FinBERT"开关。
- 顶部 5 档着色总评(1 深红…5 深绿) + stance 文案 + 正/中/负条数。
- LLM 总结段(若有)，下面每条新闻:stance 小徽章 + 标题(链接) + 一句理由 + 来源/时间。
- 明确免责："AI 解读，非投资建议;实时快照,非回测特征。"
- loading/error 用 getApiDisplayMessage;数值/配色沿用现有主题。
- lib/api.ts 加 runNewsSentiment(params)；类型齐全。i18n 中英文文案。
tsc+test+build 全绿。
```

---

## 三条红线(务必写进代码注释与 UI 文案)
1. **未来函数**：这是**当前实时面板**，不作为历史回测特征。要当特征必须 point-in-time 历史新闻，另说。
2. **情感≠alpha**：作为背景/洞察呈现,不做收益预测。
3. **分类归分类、解释归解释**：档位来自确定性分类器(词典/FinBERT)，LLM 只做带引用的解释,不下判断、不预测。

## 加分(可选 AIN-5)
```
让 LLM 也对同一批新闻打个情感,与词典/FinBERT 的档位算**一致率(agreement)**并展示,
体现"评估模型、不盲信 LLM"的意识——面试很讨喜。
```
