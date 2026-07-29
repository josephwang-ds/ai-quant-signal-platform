/**
 * Information Architecture V2 — presentation contracts only.
 * No invented market quotes, rankings, or portfolio metrics.
 */

import {
  PRODUCT_NAME,
  PRODUCT_NAME_ZH,
  PRODUCT_PHILOSOPHY,
  PRODUCT_PHILOSOPHY_ZH,
  PRODUCT_TAGLINE,
  PRODUCT_TAGLINE_ZH,
} from "@/lib/productIdentity";

export const PLATFORM = {
  nameEn: PRODUCT_NAME,
  nameZh: PRODUCT_NAME_ZH,
  taglineEn: PRODUCT_TAGLINE,
  taglineZh: PRODUCT_TAGLINE_ZH,
  principleEn: PRODUCT_PHILOSOPHY,
  principleZh: PRODUCT_PHILOSOPHY_ZH,
} as const;

export const US_LIQUID_31_SYMBOLS = [
  "AAPL",
  "MSFT",
  "NVDA",
  "AMZN",
  "GOOGL",
  "META",
  "TSLA",
  "BRK-B",
  "JPM",
  "V",
  "MA",
  "UNH",
  "XOM",
  "JNJ",
  "PG",
  "COST",
  "HD",
  "ABBV",
  "KO",
  "PEP",
  "MRK",
  "AVGO",
  "CRM",
  "AMD",
  "NFLX",
  "WMT",
  "BAC",
  "ORCL",
  "CVX",
  "ADBE",
  "MU",
] as const;

export const UNIVERSE_PREVIEW_SYMBOLS = US_LIQUID_31_SYMBOLS.slice(0, 6);

export type EngineStageStatus = "completed" | "current" | "locked";

export type EngineStageId =
  | "setup"
  | "data"
  | "features"
  | "factors"
  | "modeling"
  | "portfolio"
  | "backtest"
  | "review";

export type EngineStage = {
  id: EngineStageId;
  number: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
  status: EngineStageStatus;
  titleEn: string;
  titleZh: string;
  purposeEn: string;
  purposeZh: string;
  inputsEn: readonly string[];
  inputsZh: readonly string[];
  methodsEn: readonly string[];
  methodsZh: readonly string[];
  outputsEn: readonly string[];
  outputsZh: readonly string[];
  evidenceEn: readonly string[];
  evidenceZh: readonly string[];
  limitationsEn: readonly string[];
  limitationsZh: readonly string[];
  /** Former standalone experiment surfaces absorbed here. */
  absorbsEn?: readonly string[];
  absorbsZh?: readonly string[];
  /** Existing product tools reachable without inventing new backends. */
  toolHrefs?: readonly { href: string; labelEn: string; labelZh: string }[];
};

export const FLAGSHIP_RESEARCH = {
  id: "cross-sectional-equity-research",
  nameEn: "Cross-Sectional Equity Research",
  nameZh: "横截面股票研究",
  universe: "US Liquid 31",
  dataFrequencyEn: "Daily OHLCV",
  dataFrequencyZh: "日频 OHLCV",
  factorsEn: "Momentum / Risk / Liquidity",
  factorsZh: "动量 / 风险 / 流动性",
  labelsEn: "5D / 20D forward return",
  labelsZh: "5 日 / 20 日前向收益",
  verifiedThroughEn: "Phase 1–3 verified",
  verifiedThroughZh: "Phase 1–3 已验证",
  nextEn: "Phase 4 next — Portfolio Construction",
  nextZh: "下一步：Phase 4 — 组合构建",
} as const;

/**
 * Flagship engine path. Stages 1–5 complete (Setup → Modeling).
 * Portfolio is current; Backtest and Review remain locked.
 */
export const ENGINE_STAGES: readonly EngineStage[] = [
  {
    id: "setup",
    number: 1,
    status: "completed",
    titleEn: "Research Setup",
    titleZh: "研究设定",
    purposeEn:
      "Define the research question, universe, horizon, and evaluation protocol before any modeling.",
    purposeZh: "在任何建模前，明确研究问题、股票池、horizon 与评估协议。",
    inputsEn: ["Research hypothesis", "Universe policy", "Label horizon"],
    inputsZh: ["研究假设", "股票池策略", "标签 horizon"],
    methodsEn: ["Written research definition", "Static demo universe disclosure"],
    methodsZh: ["书面研究定义", "静态演示股票池披露"],
    outputsEn: ["Frozen research configuration"],
    outputsZh: ["冻结的研究配置"],
    evidenceEn: [
      "Research name: Cross-Sectional Equity Research",
      "Universe: US Liquid 31 (static demo)",
      "Horizon labels: 5D / 20D forward return",
      "Factor families: Momentum · Risk · Liquidity",
    ],
    evidenceZh: [
      "研究名称：横截面股票研究",
      "股票池：US Liquid 31（静态演示）",
      "标签 horizon：5 日 / 20 日前向收益",
      "因子族：动量 · 风险 · 流动性",
    ],
    limitationsEn: [
      "Universe is a manually configured demonstration list — not point-in-time index membership.",
      "Survivorship bias is not corrected.",
    ],
    limitationsZh: [
      "股票池为人工演示名单，不是时点指数成分。",
      "未校正幸存者偏差。",
    ],
  },
  {
    id: "data",
    number: 2,
    status: "completed",
    titleEn: "Data Foundation",
    titleZh: "数据基础",
    purposeEn: "Assemble point-in-time market inputs suitable for reproducible research.",
    purposeZh: "组装可用于可复现研究的时点市场输入。",
    inputsEn: ["Daily OHLCV", "Configured universe membership"],
    inputsZh: ["日频 OHLCV", "已配置股票池成员"],
    methodsEn: ["Dataset API", "Coverage and quality checks"],
    methodsZh: ["数据集 API", "覆盖与质量检查"],
    outputsEn: ["Research-ready price panel"],
    outputsZh: ["研究可用价格面板"],
    evidenceEn: [
      "Phase 1 dataset API verified",
      "Daily OHLCV for US Liquid 31",
      "Quality and coverage checks recorded",
    ],
    evidenceZh: [
      "Phase 1 数据集 API 已验证",
      "US Liquid 31 日频 OHLCV",
      "质量与覆盖检查已记录",
    ],
    limitationsEn: ["Live streaming market data is out of scope for this shell."],
    limitationsZh: ["本壳层不包含实时流式行情。"],
    toolHrefs: [
      {
        href: "/data-center",
        labelEn: "Open Data Center coverage",
        labelZh: "打开数据中心覆盖说明",
      },
    ],
  },
  {
    id: "features",
    number: 3,
    status: "completed",
    titleEn: "Feature Engineering",
    titleZh: "特征工程",
    purposeEn:
      "Transform raw market inputs into point-in-time features and forward-return labels.",
    purposeZh: "将原始市场输入转为时点特征与前向收益标签。",
    inputsEn: ["OHLCV panel", "Factor family definitions", "Label horizons"],
    inputsZh: ["OHLCV 面板", "因子族定义", "标签 horizon"],
    methodsEn: ["Point-in-time feature panel construction", "Forward-return labeling"],
    methodsZh: ["时点特征面板构建", "前向收益打标"],
    outputsEn: ["Factor panel", "5D / 20D labels"],
    outputsZh: ["因子面板", "5 日 / 20 日标签"],
    evidenceEn: [
      "Phase 1 factor panel construction verified",
      "Labels aligned to 5D / 20D forward returns",
    ],
    evidenceZh: [
      "Phase 1 因子面板构建已验证",
      "标签对齐 5 日 / 20 日前向收益",
    ],
    limitationsEn: [
      "Feature store / streaming feature services are not part of this demonstration.",
    ],
    limitationsZh: ["本演示不包含特征存储或流式特征服务。"],
    toolHrefs: [
      {
        href: "/feature-interpretation",
        labelEn: "Open feature interpretation utility",
        labelZh: "打开特征解释工具",
      },
    ],
  },
  {
    id: "factors",
    number: 4,
    status: "completed",
    titleEn: "Factor Research",
    titleZh: "因子研究",
    purposeEn: "Evaluate individual factors with RankIC, quantiles, turnover, and stability.",
    purposeZh: "用 RankIC、分组、换手与稳定性评估单因子。",
    inputsEn: ["Factor panel", "Forward-return labels"],
    inputsZh: ["因子面板", "前向收益标签"],
    methodsEn: ["Daily RankIC", "Quantile returns", "Calendar-year stability"],
    methodsZh: ["日度 RankIC", "分组收益", "日历年稳定性"],
    outputsEn: ["Factor research evidence packages"],
    outputsZh: ["因子研究证据包"],
    evidenceEn: [
      "Phase 2 factor research API verified",
      "Daily RankIC (not pooled)",
      "Quantile returns and turnover",
    ],
    evidenceZh: [
      "Phase 2 因子研究 API 已验证",
      "日度 RankIC（不跨日池化）",
      "分组收益与换手",
    ],
    limitationsEn: [
      "Dedicated US Liquid 31 factor UI is still limited; interactive Factor Study remains available.",
    ],
    limitationsZh: [
      "US Liquid 31 专用因子 UI 仍有限；交互式因子研究路径仍可用。",
    ],
    absorbsEn: ["Momentum parameter studies", "Factor sensitivity screens"],
    absorbsZh: ["动量参数研究", "因子敏感性筛查"],
  },
  {
    id: "modeling",
    number: 5,
    status: "completed",
    titleEn: "Modeling",
    titleZh: "建模排序",
    purposeEn:
      "Train leakage-safe walk-forward models that produce out-of-sample stock scores.",
    purposeZh: "训练防泄漏 walk-forward 模型，产出样本外股票评分。",
    inputsEn: ["Verified factor panel", "Approved labels"],
    inputsZh: ["已验证因子面板", "已批准标签"],
    methodsEn: ["Ridge baseline", "LightGBM candidate", "Walk-forward scoring"],
    methodsZh: ["Ridge 基线", "LightGBM 候选", "Walk-forward 评分"],
    outputsEn: ["Out-of-sample scores and ranks"],
    outputsZh: ["样本外评分与排序"],
    evidenceEn: [
      "Phase 3 modeling API verified",
      "Ridge baseline + LightGBM candidate",
      "447 non-live backend tests passing",
    ],
    evidenceZh: [
      "Phase 3 建模 API 已验证",
      "Ridge 基线 + LightGBM 候选",
      "447 项非 live 后端测试通过",
    ],
    limitationsEn: ["Scores are research artifacts — not trade recommendations."],
    limitationsZh: ["评分为研究产物，不是交易建议。"],
    absorbsEn: ["Model comparison utilities"],
    absorbsZh: ["模型对比工具"],
    toolHrefs: [
      {
        href: "/compare-models",
        labelEn: "Open model comparison",
        labelZh: "打开模型对比",
      },
    ],
  },
  {
    id: "portfolio",
    number: 6,
    status: "current",
    titleEn: "Portfolio Construction",
    titleZh: "组合构建",
    purposeEn: "Convert scores into constrained portfolio weights under explicit rules.",
    purposeZh: "在明确规则下，将评分转为带约束的组合权重。",
    inputsEn: ["Out-of-sample scores", "Risk and capacity constraints"],
    inputsZh: ["样本外评分", "风险与容量约束"],
    methodsEn: ["Top-K selection (planned)", "Weighting and constraints (planned)"],
    methodsZh: ["Top-K 选股（计划中）", "权重与约束（计划中）"],
    outputsEn: ["Portfolio weights (not yet produced)"],
    outputsZh: ["组合权重（尚未产出）"],
    evidenceEn: [
      "No portfolio weights yet",
      "No Top-K selection yet",
      "No position sizing yet",
    ],
    evidenceZh: ["尚无组合权重", "尚无 Top-K 选股", "尚无仓位缩放"],
    limitationsEn: ["Phase 4 backend logic is intentionally not implemented in this build."],
    limitationsZh: ["本构建有意不实现 Phase 4 后端逻辑。"],
    absorbsEn: ["Allocation sensitivity experiments"],
    absorbsZh: ["配置敏感性实验"],
  },
  {
    id: "backtest",
    number: 7,
    status: "locked",
    titleEn: "Backtesting",
    titleZh: "回测",
    purposeEn: "Evaluate portfolio behavior under costs, turnover, and robustness checks.",
    purposeZh: "在成本、换手与稳健性检验下评估组合行为。",
    inputsEn: ["Portfolio weights", "Cost assumptions", "Benchmark policy"],
    inputsZh: ["组合权重", "成本假设", "基准策略"],
    methodsEn: ["Historical simulation (planned)", "Cost and stress suites (planned)"],
    methodsZh: ["历史模拟（计划中）", "成本与压力套件（计划中）"],
    outputsEn: ["Backtest evidence packages (not yet produced)"],
    outputsZh: ["回测证据包（尚未产出）"],
    evidenceEn: ["No backtest PnL yet", "No cost / turnover portfolio metrics yet"],
    evidenceZh: ["尚无回测 PnL", "尚无组合成本 / 换手指标"],
    limitationsEn: ["Locked until Portfolio Construction exists."],
    limitationsZh: ["组合构建完成前锁定。"],
    absorbsEn: [
      "Transaction cost analysis",
      "Stress testing",
      "Saved strategy runs",
      "Robustness suites",
    ],
    absorbsZh: ["交易成本分析", "压力测试", "已存策略运行", "稳健性套件"],
    toolHrefs: [
      {
        href: "/strategy-lab",
        labelEn: "Open Strategy Studio (legacy single-asset lab)",
        labelZh: "打开策略工作室（遗留单标的实验室）",
      },
      {
        href: "/robustness",
        labelEn: "Open robustness utilities",
        labelZh: "打开稳健性工具",
      },
    ],
  },
  {
    id: "review",
    number: 8,
    status: "locked",
    titleEn: "Research Review",
    titleZh: "研究审阅",
    purposeEn: "Human Promote / Hold / Reject decisions grounded in accumulated evidence.",
    purposeZh: "基于累积证据的人工 Promote / Hold / Reject 决策。",
    inputsEn: ["Full evidence trail from prior stages"],
    inputsZh: ["此前各阶段的完整证据链"],
    methodsEn: ["Governed human review", "Traceable decision records"],
    methodsZh: ["受治理的人工审阅", "可追溯决策记录"],
    outputsEn: ["Review decision (not yet recorded)"],
    outputsZh: ["审阅决策（尚未记录）"],
    evidenceEn: ["No governance decision recorded for this flagship workflow yet"],
    evidenceZh: ["本旗舰流程尚无治理决策记录"],
    limitationsEn: ["Locked until backtest evidence exists."],
    limitationsZh: ["回测证据齐备前锁定。"],
  },
] as const;

export type IntelligenceModuleId =
  | "market"
  | "research"
  | "signal"
  | "portfolio"
  | "risk"
  | "assistant";

export type IntelligenceModule = {
  id: IntelligenceModuleId;
  href: string;
  titleEn: string;
  titleZh: string;
  questionEn: string;
  questionZh: string;
  /** Honest status — never invents unsupported conclusions. */
  statusEn: string;
  statusZh: string;
  evidencePathEn: string;
  evidencePathZh: string;
  engineHref: string;
};

export const INTELLIGENCE_MODULES: readonly IntelligenceModule[] = [
  {
    id: "market",
    href: "/intelligence/market",
    titleEn: "Market Intelligence",
    titleZh: "市场智能",
    questionEn: "What is happening in the market context?",
    questionZh: "市场语境正在发生什么？",
    statusEn:
      "No AI market narrative is published without grounded market data and research context.",
    statusZh: "没有 grounded 市场数据与研究语境时，不发布 AI 市场叙事。",
    evidencePathEn: "Market data → Research Engine context → Evidence → LLM summary",
    evidencePathZh: "市场数据 → 研究引擎语境 → 证据 → LLM 摘要",
    engineHref: "/engine/data",
  },
  {
    id: "research",
    href: "/intelligence/research",
    titleEn: "Research Intelligence",
    titleZh: "研究智能",
    questionEn: "Where does current research stand?",
    questionZh: "当前研究进展到哪里？",
    statusEn:
      "Flagship Cross-Sectional Equity Research: Phase 1–3 verified; Portfolio Construction is next.",
    statusZh: "旗舰横截面股票研究：Phase 1–3 已验证；下一步为组合构建。",
    evidencePathEn: "Engine stage status → Evidence packages → LLM progress summary",
    evidencePathZh: "引擎阶段状态 → 证据包 → LLM 进展摘要",
    engineHref: "/engine",
  },
  {
    id: "signal",
    href: "/intelligence/signal",
    titleEn: "Signal Intelligence",
    titleZh: "信号智能",
    questionEn: "Which opportunities are ranked — and why?",
    questionZh: "哪些机会被排序——依据是什么？",
    statusEn:
      "Model scores exist in Modeling. Ranked opportunity cards are withheld until Portfolio Construction evidence exists.",
    statusZh:
      "建模阶段已有评分。在组合构建证据出现前，不发布机会排序卡片。",
    evidencePathEn: "Ranking model → Risk filters → Portfolio constraints → LLM explanation",
    evidencePathZh: "排序模型 → 风险过滤 → 组合约束 → LLM 解释",
    engineHref: "/engine/modeling",
  },
  {
    id: "portfolio",
    href: "/intelligence/portfolio",
    titleEn: "Portfolio Intelligence",
    titleZh: "组合智能",
    questionEn: "What is current portfolio health?",
    questionZh: "当前组合健康度如何？",
    statusEn: "No portfolio weights or health metrics are available yet.",
    statusZh: "尚无组合权重或健康度指标。",
    evidencePathEn: "Portfolio Construction → Weights → Holdings evidence → LLM review",
    evidencePathZh: "组合构建 → 权重 → 持仓证据 → LLM 审阅",
    engineHref: "/engine/portfolio",
  },
  {
    id: "risk",
    href: "/intelligence/risk",
    titleEn: "Risk Intelligence",
    titleZh: "风险智能",
    questionEn: "What is the current risk assessment?",
    questionZh: "当前风险评估是什么？",
    statusEn: "Risk intelligence unlocks after portfolio and backtest evidence exist.",
    statusZh: "组合与回测证据齐备后，才解锁风险智能。",
    evidencePathEn: "Portfolio → Backtest → Risk metrics → LLM review",
    evidencePathZh: "组合 → 回测 → 风险指标 → LLM 审阅",
    engineHref: "/engine/backtest",
  },
  {
    id: "assistant",
    href: "/intelligence/assistant",
    titleEn: "AI Research Assistant",
    titleZh: "AI 研究助手",
    questionEn: "Ask grounded questions about research evidence and documentation.",
    questionZh: "针对研究证据与文档提出 grounded 问题。",
    statusEn:
      "Assistant responses must cite research evidence or documentation — never unsupported opinions.",
    statusZh: "助手回答必须引用研究证据或文档——禁止无依据观点。",
    evidencePathEn: "RAG over research evidence + documentation → Grounded answers",
    evidencePathZh: "研究证据与文档 RAG → Grounded 回答",
    engineHref: "/engine/review",
  },
] as const;

export function getCurrentEngineStage(
  stages: readonly EngineStage[] = ENGINE_STAGES
): EngineStage {
  return stages.find((stage) => stage.status === "current") ?? stages[0];
}

export function getContinueTarget(
  stages: readonly EngineStage[] = ENGINE_STAGES
): EngineStage {
  return getCurrentEngineStage(stages);
}

export function getEngineStage(
  id: string,
  stages: readonly EngineStage[] = ENGINE_STAGES
): EngineStage | undefined {
  return stages.find((stage) => stage.id === id);
}

export function stageStatusLabel(
  status: EngineStageStatus,
  language: "en" | "zh"
): string {
  if (language === "zh") {
    if (status === "completed") return "已完成";
    if (status === "current") return "当前";
    return "锁定";
  }
  if (status === "completed") return "Completed";
  if (status === "current") return "Current";
  return "Locked";
}

export function getIntelligenceModule(
  id: string
): IntelligenceModule | undefined {
  return INTELLIGENCE_MODULES.find((module) => module.id === id);
}

/** @deprecated Prefer ENGINE_STAGES */
export const WORKFLOW_STAGES = ENGINE_STAGES;
