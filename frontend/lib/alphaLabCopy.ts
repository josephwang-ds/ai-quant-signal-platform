/**
 * Copy for the Alpha Research Lab (`/alpha-lab`).
 *
 * Extracted from the component because the page carries multi-sentence prose,
 * and forty inline `zh ? … : …` ternaries around paragraphs is unreadable.
 * Short shared labels (navigation, chrome) still live in `lib/i18n.ts`; this
 * module is page-level copy only, matching how `ResearchLibraryPage` and
 * `PlatformHomePage` keep their own strings local.
 *
 * Known gap: `capm.decomposition.methodology` arrives from the backend in
 * English. It is service-authored evidence provenance rather than UI chrome, so
 * it is rendered as received instead of being re-translated client-side — a
 * translated copy would drift from what the service actually did.
 */

import type { Language } from "@/lib/i18n";

export type AlphaLabCopy = {
  eyebrow: string;
  breadcrumb: string;
  kicker: string;
  title: string;
  decisionPrefix: string;
  decisions: { promote: string; hold: string; reject: string };
  question: string;
  metaMonthly: string;
  metaForward: (months: number) => string;
  metaChronological: string;
  metaBenchmark: string;
  scopeLine: string;
  loading: string;
  unavailable: string;
  fetchError: string;
  tabs: Record<
    "question" | "data" | "alpha" | "portfolio" | "attribution",
    string
  >;
  sections: {
    information: string;
    costs: string;
    alphaOrBeta: string;
    stability: string;
  };
  stats: {
    meanRankIc: string;
    meanRankIcCaption: string;
    icir: string;
    icirCaption: string;
    positiveIc: string;
    positiveIcCaption: (n: number) => string;
    grossSpread: string;
    grossSpreadCaption: string;
    netSpread: string;
    netSpreadCaption: string;
    turnover: string;
    turnoverCaption: string;
    netAlpha: string;
    netAlphaCaption: (low: string, high: string) => string;
    tstat: string;
    tstatCaption: (n: number) => string;
    beta: string;
    betaCaption: (benchmark: string) => string;
    rSquared: string;
    rSquaredCaption: string;
    sharpe: string;
    sharpeCaption: string;
    maxDrawdown: string;
    maxDrawdownCaption: string;
  };
  provenance: (universe: string, benchmark: string, from: string, to: string) => string;
  chart: {
    title: string;
    subtitle: string;
    costDrag: string;
    betaContribution: string;
    residualAlpha: string;
    /**
     * Localized rendering of the service's `methodology` note.
     *
     * `null` means "render the string the API returned verbatim". English does
     * that, so the service stays the single source of truth for what it
     * actually computed. Chinese supplies a maintained translation, because a
     * paragraph of English in the middle of a Chinese page is its own kind of
     * unreadable. Keep the Chinese text in sync with
     * `decompose_performance()` in `backend/app/factor_validation/capm.py`.
     */
    methodology: string | null;
  };
  questionTab: {
    heading: string;
    lede: string;
    findings: Array<{ lead: string; body: string }>;
    decisionLine: (decision: string, verdict: string) => string;
    scopeNote: string;
  };
  dataTab: {
    heading: string;
    universe: string;
    universeValue: (used: number, total: number) => string;
    dateRange: string;
    latest: string;
    factorPeriods: string;
    benchmark: string;
    warnings: string;
    noWarnings: string;
  };
  notBuilt: {
    portfolioTitle: string;
    portfolioNote: string;
    attributionTitle: string;
    attributionNote: string;
  };
  pipelineRecap: (decision: string) => string;
};

const EN: AlphaLabCopy = {
  eyebrow: "Alpha Research Lab",
  breadcrumb: "Signal → Attribution",
  kicker: "Cross-sectional equity research",
  title: "Momentum alpha after beta and costs",
  decisionPrefix: "Decision",
  decisions: { promote: "Promote", hold: "Hold", reject: "Reject" },
  question:
    "Does momentum retain predictive power after neutralizing market beta and charging turnover costs?",
  metaMonthly: "Monthly rebalance",
  metaForward: (m) => `Forward ${m}M return`,
  metaChronological: "Chronological, no shuffling",
  metaBenchmark: "Benchmark",
  scopeLine:
    "Price-only baseline · control arm for the text-signals track — not individual stock advice",
  loading: "Loading real factor-validation evidence…",
  unavailable: "Unavailable.",
  fetchError:
    "Factor validation is unavailable. Invented evidence is not shown.",
  tabs: {
    question: "Research question",
    data: "Data & signals",
    alpha: "Alpha validation",
    portfolio: "Portfolio & beta",
    attribution: "Attribution & monitor",
  },
  sections: {
    information: "Does the signal carry information?",
    costs: "Does it survive costs?",
    alphaOrBeta: "Is it alpha or beta?",
    stability: "Stable enough to trust?",
  },
  stats: {
    meanRankIc: "Mean RankIC",
    meanRankIcCaption: "out-of-sample only",
    icir: "ICIR",
    icirCaption: "mean IC / std IC",
    positiveIc: "Positive IC ratio",
    positiveIcCaption: (n) => `of ${n} periods`,
    grossSpread: "Q5 − Q1 gross",
    grossSpreadCaption: "before transaction costs",
    netSpread: "Q5 − Q1 net",
    netSpreadCaption: "after transaction costs",
    turnover: "Turnover",
    turnoverCaption: "cost pressure per rebalance",
    netAlpha: "Net alpha",
    netAlphaCaption: (low, high) => `95% CI ${low} to ${high}`,
    tstat: "Alpha t-stat",
    tstatCaption: (n) => `n = ${n} periods`,
    beta: "Market beta",
    betaCaption: (b) => `vs ${b}`,
    rSquared: "R²",
    rSquaredCaption: "variance explained by beta",
    sharpe: "Sharpe (net)",
    sharpeCaption: "annualized, long-short book",
    maxDrawdown: "Max drawdown (net)",
    maxDrawdownCaption: "peak to trough",
  },
  provenance: (universe, benchmark, from, to) =>
    `Source: factor_validation service · ${universe} vs ${benchmark} · ${from} → ${to}`,
  chart: {
    title: "Where did performance come from?",
    subtitle:
      "Long-short portfolio return decomposed into beta contribution, residual alpha, and cost drag",
    costDrag: "Cost drag",
    betaContribution: "Beta contribution",
    residualAlpha: "Residual alpha",
    methodology: null,
  },
  questionTab: {
    heading: "Why this question",
    lede:
      "Individual investors can generate signals faster than they can validate them. This page exists to slow that down, on purpose.",
    findings: [
      {
        lead: "No repeatable research process.",
        body:
          "The question, success criteria, and benchmark are fixed above before any result is shown — universe, rebalance frequency, and forward window are stated, not chosen after the fact.",
      },
      {
        lead: "Outperformance isn’t automatically alpha.",
        body:
          "The stats below regress this factor’s returns against a market benchmark to separate residual alpha from beta exposure — see Market beta and the decomposition chart on the Alpha Validation tab.",
      },
      {
        lead: "Evidence decays after publication.",
        body:
          "Rolling IC/alpha-decay monitoring is not built yet — the Attribution & Monitor tab says so honestly rather than faking a chart.",
      },
    ],
    decisionLine: (decision, verdict) =>
      `Current decision: ${decision} — derived directly from the factor benchmark verdict (${verdict}), not a separately fabricated judgment.`,
    scopeNote:
      "Scope: this system validates cross-sectional factor and portfolio evidence. It does not generate single-stock buy/sell signals — any per-symbol membership shown elsewhere is transparency, not a recommendation.",
  },
  dataTab: {
    heading: "Data & signals",
    universe: "Universe",
    universeValue: (used, total) => `${used} symbols used of ${total}`,
    dateRange: "Date range",
    latest: "latest",
    factorPeriods: "Factor periods",
    benchmark: "Benchmark",
    warnings: "Warnings",
    noWarnings: "No data-quality warnings for this run.",
  },
  notBuilt: {
    portfolioTitle: "Portfolio & beta — not yet built",
    portfolioNote:
      "Sector and style neutralization at the portfolio level maps to this repo's own not-yet-started Phase 5.2 (Portfolio Exposure Snapshots). The Alpha Validation tab already shows a real single-factor market-beta regression on the long-short portfolio; this tab will extend that to multi-member portfolios with sector/style exposure once that phase lands.",
    attributionTitle: "Attribution & monitor — not yet built",
    attributionNote:
      "Rolling IC/alpha-decay monitoring and portfolio-level alpha/beta/sector attribution do not exist yet in this codebase — the post-trade module computes execution/cost attribution (fees, slippage, venue), a related but distinct question. This tab is reserved for that future slice.",
  },
  pipelineRecap: (decision) =>
    `Question → Data → Alpha Validation → Portfolio & Beta (planned) → Attribution & Monitor (planned) → Decision: ${decision}`,
};

const ZH: AlphaLabCopy = {
  eyebrow: "Alpha 研究实验室",
  breadcrumb: "信号 → 归因",
  kicker: "横截面股票研究",
  title: "剔除 Beta 与成本后的动量 Alpha",
  decisionPrefix: "结论",
  decisions: { promote: "推进", hold: "暂缓", reject: "否决" },
  question:
    "在中性化市场 Beta 并计入换手成本之后，动量是否仍保有预测能力？",
  metaMonthly: "月度调仓",
  metaForward: (m) => `前向 ${m} 个月收益`,
  metaChronological: "严格按时间顺序，不打乱样本",
  metaBenchmark: "基准",
  scopeLine:
    "纯价格基线 · 文本信号轨道的对照臂 —— 不构成个股投资建议",
  loading: "正在加载真实的因子验证证据…",
  unavailable: "暂不可用。",
  fetchError: "因子验证暂不可用。不会展示编造的证据。",
  tabs: {
    question: "研究问题",
    data: "数据与信号",
    alpha: "Alpha 验证",
    portfolio: "组合与 Beta",
    attribution: "归因与监控",
  },
  sections: {
    information: "信号本身有信息量吗？",
    costs: "扣除成本后还站得住吗？",
    alphaOrBeta: "这是 Alpha 还是 Beta？",
    stability: "稳定到值得相信吗？",
  },
  stats: {
    meanRankIc: "RankIC 均值",
    meanRankIcCaption: "仅样本外",
    icir: "ICIR",
    icirCaption: "IC 均值 / IC 标准差",
    positiveIc: "IC 为正的比例",
    positiveIcCaption: (n) => `共 ${n} 期`,
    grossSpread: "Q5 − Q1 毛收益",
    grossSpreadCaption: "扣除交易成本前",
    netSpread: "Q5 − Q1 净收益",
    netSpreadCaption: "扣除交易成本后",
    turnover: "换手率",
    turnoverCaption: "每次调仓的成本压力",
    netAlpha: "净 Alpha",
    netAlphaCaption: (low, high) => `95% 置信区间 ${low} 至 ${high}`,
    tstat: "Alpha t 统计量",
    tstatCaption: (n) => `n = ${n} 期`,
    beta: "市场 Beta",
    betaCaption: (b) => `对 ${b}`,
    rSquared: "R²",
    rSquaredCaption: "由 Beta 解释的方差比例",
    sharpe: "夏普比率（净）",
    sharpeCaption: "年化，多空组合",
    maxDrawdown: "最大回撤（净）",
    maxDrawdownCaption: "峰值到谷底",
  },
  provenance: (universe, benchmark, from, to) =>
    `来源：factor_validation 服务 · ${universe} 对比 ${benchmark} · ${from} → ${to}`,
  chart: {
    title: "收益究竟从哪里来？",
    subtitle: "多空组合收益拆解为 Beta 贡献、残差 Alpha 与成本拖累",
    costDrag: "成本拖累",
    betaContribution: "Beta 贡献",
    residualAlpha: "残差 Alpha",
    methodology:
      "加性近似：每期扣除成本后的多空净收益被拆为 beta × 基准收益（Beta 贡献）与净收益减去该贡献的部分（残差 Alpha），两者的累计和精确等于累计净收益。成本拖累（毛收益减净收益）作为单独的纯参考序列展示，并非第三个加性项。这些是收益点的滚动求和，不是几何复利，应当理解为对收益来源的拆解，而不是复利后的财富曲线。",
  },
  questionTab: {
    heading: "为什么问这个问题",
    lede:
      "个人投资者生成信号的速度，已经超过了验证信号的能力。这个页面的存在就是为了刻意把这个过程放慢。",
    findings: [
      {
        lead: "缺少可重复的研究流程。",
        body:
          "研究问题、成功标准与基准都在任何结果出现之前就已在上方固定——股票池、调仓频率与前向窗口是事先声明的，不是事后挑选的。",
      },
      {
        lead: "跑赢不等于就是 Alpha。",
        body:
          "下方统计量把该因子的收益对市场基准做回归，以区分残差 Alpha 与 Beta 暴露——见「Alpha 验证」标签中的市场 Beta 与拆解图。",
      },
      {
        lead: "证据会在发布之后衰减。",
        body:
          "滚动 IC / Alpha 衰减监控尚未建成——「归因与监控」标签会如实说明这一点，而不是伪造一张图表。",
      },
    ],
    decisionLine: (decision, verdict) =>
      `当前结论：${decision} —— 直接由因子基准判定（${verdict}）推导得出，并非另行编造的判断。`,
    scopeNote:
      "范围：本系统验证的是横截面因子与组合层面的证据，不生成个股买卖信号——其他页面展示的成分股仅为透明度说明，不构成推荐。",
  },
  dataTab: {
    heading: "数据与信号",
    universe: "股票池",
    universeValue: (used, total) => `共 ${total} 只，实际使用 ${used} 只`,
    dateRange: "日期区间",
    latest: "至最新",
    factorPeriods: "因子期数",
    benchmark: "基准",
    warnings: "警告",
    noWarnings: "本次运行没有数据质量警告。",
  },
  notBuilt: {
    portfolioTitle: "组合与 Beta —— 尚未建成",
    portfolioNote:
      "组合层面的行业与风格中性化，对应本仓库自身尚未启动的 Phase 5.2（组合暴露快照）。「Alpha 验证」标签已经展示了对多空组合做的真实单因子市场 Beta 回归；待该阶段落地后，本标签会将其扩展到含行业/风格暴露的多成分组合。",
    attributionTitle: "归因与监控 —— 尚未建成",
    attributionNote:
      "滚动 IC / Alpha 衰减监控，以及组合层面的 Alpha/Beta/行业归因，在本代码库中尚不存在——post-trade 模块计算的是执行与成本归因（费用、滑点、交易场所），是相关但不同的问题。本标签为后续切片预留。",
  },
  pipelineRecap: (decision) =>
    `研究问题 → 数据 → Alpha 验证 → 组合与 Beta（计划中）→ 归因与监控（计划中）→ 结论：${decision}`,
};

export function alphaLabCopy(language: Language): AlphaLabCopy {
  return language === "zh" ? ZH : EN;
}
