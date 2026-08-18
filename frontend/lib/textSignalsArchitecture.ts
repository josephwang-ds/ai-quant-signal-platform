/**
 * Text Signals track — presentation contracts only.
 *
 * The repositioning this encodes: the signal channel is text (SEC filings), not
 * price, and the measured quantity is *incremental information value over a
 * price-only baseline*, not excess return. See `docs/HANDOFF_TEXT_SIGNALS.md`.
 *
 * Two rules this file exists to enforce structurally rather than by good
 * intentions:
 *
 * 1. **Status is honest.** An experiment that has not run says so. The one
 *    thing this project sells is a verdict framework that can reject its own
 *    work, so manufactured progress here would be self-defeating.
 * 2. **No result numbers live here.** Not even as examples. Pre-writing plausible
 *    figures anchors the reader — and the author — before the evidence exists.
 */

export type ExperimentStatus = "in_progress" | "not_started" | "complete";

export type ExperimentStep = {
  id: string;
  labelEn: string;
  labelZh: string;
  done: boolean;
};

export type TextSignalExperiment = {
  id: "A" | "B" | "C";
  /** What this experiment is *for* in the overall argument. */
  roleEn: string;
  roleZh: string;
  titleEn: string;
  titleZh: string;
  questionEn: string;
  questionZh: string;
  status: ExperimentStatus;
  /** Present only where a step breakdown genuinely exists. */
  steps?: readonly ExperimentStep[];
  /** Honest one-liner about where this stands. Never aspirational. */
  statusNoteEn: string;
  statusNoteZh: string;
};

/**
 * The subtraction ladder. Each rung removes a competing explanation, and what
 * survives all of them is the quantity of interest.
 *
 * This is the whole argument for the repositioning: "does this beat the market?"
 * is unanswerable on free data, while "does this text channel add information
 * over price?" is answerable — both arms span the same periods and carry the
 * same trading assumptions, so cost largely cancels in the contrast.
 */
export const SUBTRACTION_LADDER = [
  {
    subtractEn: "raw return",
    subtractZh: "原始收益",
    yieldsEn: "starting point",
    yieldsZh: "起点",
  },
  {
    subtractEn: "− benchmark return",
    subtractZh: "− 基准收益",
    yieldsEn: "excess return",
    yieldsZh: "超额收益",
  },
  {
    subtractEn: "− exposure to known factors (mkt / size / mom / vol)",
    subtractZh: "− 已知因子暴露（市场 / 规模 / 动量 / 波动）",
    yieldsEn: "residual return",
    yieldsZh: "残差收益",
  },
  {
    subtractEn: "− trading cost",
    subtractZh: "− 交易成本",
    yieldsEn: "net residual",
    yieldsZh: "成本后残差",
  },
  {
    subtractEn: "− everything predictable from price history alone",
    subtractZh: "− 仅凭价格历史即可预测的部分",
    yieldsEn: "incremental signal value",
    yieldsZh: "增量信号价值",
    terminal: true,
  },
] as const;

export const TEXT_SIGNAL_EXPERIMENTS: readonly TextSignalExperiment[] = [
  {
    id: "A",
    roleEn: "the substrate",
    roleZh: "研究基底",
    titleEn: "Filing-change effect, modern sample",
    titleZh: "申报文本变化效应（现代样本）",
    questionEn:
      "Does a documented filing-change effect still exist after publication and during the LLM era?",
    questionZh: "已发表的申报文本变化效应，在发表之后与 LLM 时代是否依然存在？",
    status: "in_progress",
    steps: [
      {
        id: "A1",
        labelEn: "Real EDGAR fetcher",
        labelZh: "真实 EDGAR 抓取器",
        done: true,
      },
      {
        id: "A2",
        labelEn: "Document retrieval and section extraction",
        labelZh: "文档获取与章节提取",
        done: true,
      },
      {
        id: "A3",
        labelEn: "Year-over-year similarity (TF-IDF cosine)",
        labelZh: "同比相似度（TF-IDF 余弦）",
        done: true,
      },
      {
        id: "A4",
        labelEn: "Wire into the validation spine",
        labelZh: "接入验证主干",
        done: false,
      },
      {
        id: "A5",
        labelEn: "Correctness gates (planted signal, text benchmark)",
        labelZh: "正确性闸门（植入信号、文本基准）",
        done: false,
      },
      {
        id: "A6",
        labelEn: "Live collector",
        labelZh: "实时采集器",
        done: false,
      },
    ],
    statusNoteEn:
      "A1 through A3 are implemented and tested: filings are fetched from EDGAR with a declared user agent, rate limiting and an accession-keyed cache, Item 1A is extracted from real 10-K HTML — disambiguated from table-of-contents entries, cross-references and running page headers — and year-over-year TF-IDF cosine is computed same-company only, with IDF fit point-in-time so no not-yet-filed document can weight the past. No return has been computed and no return has been measured, so there is no result to report.",
    statusNoteZh:
      "A1 至 A3 已实现并有测试：带声明 User-Agent、限速与按 accession 缓存的 EDGAR 抓取，能从真实 10-K HTML 中提取 Item 1A（可与目录条目、交叉引用及页眉重复项区分开），并仅在同一公司内计算同比 TF-IDF 余弦相似度，IDF 按时点拟合，未来文件不会影响过去的权重。尚未测量任何收益，因此没有结果可报告。",
  },
  {
    id: "B",
    roleEn: "the signature",
    roleZh: "差异化标志",
    titleEn: "Inference-cost frontier",
    titleZh: "推理成本前沿",
    questionEn:
      "How much of A's signal does each extraction tier capture, and above what AUM does an expensive tier pay for itself?",
    questionZh:
      "每一档抽取模型能捕捉 A 中多少信号？在多大 AUM 之上，昂贵档位才划得来？",
    status: "not_started",
    statusNoteEn:
      "Not started. Depends on A producing a signal worth pricing. The interesting output is the break-even capital, because inference cost is fixed while capital is the denominator.",
    statusNoteZh:
      "尚未开始。取决于 A 是否产出值得定价的信号。真正有意思的输出是盈亏平衡资本量——推理成本是固定的，而资本是分母。",
  },
  {
    id: "C",
    roleEn: "the headline",
    roleZh: "最终结论",
    titleEn: "Governed agent ablation",
    titleZh: "受治理 Agent 消融实验",
    questionEn:
      "Does preregistration reduce an AI research agent's selective reporting of its own results?",
    questionZh: "预注册能否减少 AI 研究 Agent 对自身结果的选择性汇报？",
    status: "not_started",
    statusNoteEn:
      "Not started. Two arms of the same agent, matched on model, prompt context, hypothesis budget, compute and seed — the only difference is preregistration and test-set visibility.",
    statusNoteZh:
      "尚未开始。同一 Agent 的两个分支，在模型、提示上下文、假设预算、算力与随机种子上完全对齐——唯一差别是预注册与测试集可见性。",
  },
] as const;

/**
 * Constraints that must travel with any result from this track.
 *
 * These are not disclaimers added at the end; each one rules out a claim the
 * evidence cannot support, and stating them is what makes the claims that
 * remain worth anything.
 */
export const STANDING_LIMITATIONS = [
  {
    id: "C1",
    titleEn: "A modern re-test, not a replication",
    titleZh: "现代重测，而非复现",
    bodyEn:
      "The original study used CRSP, Compustat and I/B/E/S. Text is free; survivorship-safe return replication is not. Survivorship bias is a core limitation of this track, not a footnote.",
    bodyZh:
      "原研究使用 CRSP、Compustat 与 I/B/E/S。文本是免费的，但无生存者偏差的收益复现不是。生存者偏差是本track的核心限制，不是脚注。",
  },
  {
    id: "C2",
    titleEn: "No causal claim about LLMs",
    titleZh: "不对 LLM 作因果归因",
    bodyEn:
      "If the effect weakens, confounds include publication in 2020, vendor productisation, quant capital entry, regime shifts and changes in disclosure practice. This is a decay diagnosis, not causal identification.",
    bodyZh:
      "若效应减弱，混淆因素包括 2020 年的发表、厂商产品化、量化资金进入、市场状态变化与披露实践改变。这是衰减诊断，不是因果识别。",
  },
  {
    id: "C3",
    titleEn: "The quantity is not alpha",
    titleZh: "所测量的不是 Alpha",
    bodyEn:
      "Alpha is the intercept of a portfolio return regressed on a stated risk model. This track measures incremental signal value. Portfolio alpha, if wanted, is computed separately and afterwards.",
    bodyZh:
      "Alpha 是组合收益对既定风险模型回归后的截距。本 track 测量的是增量信号价值。若需要组合 Alpha，应单独另行计算。",
  },
] as const;

/** The price-only baseline this track measures *against*. */
export const PRICE_BASELINE = {
  href: "/alpha-lab",
  titleEn: "Price-only baseline",
  titleZh: "纯价格基线",
  bodyEn:
    "Cross-sectional momentum with RankIC, quantile spreads, HAC inference and a market-beta decomposition. This is the control arm: text has to add information over this, not merely beat a benchmark.",
  bodyZh:
    "横截面动量，含 RankIC、分位价差、HAC 推断与市场 Beta 分解。这是对照臂：文本必须在此之上增加信息量，而不只是跑赢基准。",
} as const;

export function experimentStatusLabel(
  status: ExperimentStatus,
  language: "en" | "zh"
): string {
  if (language === "zh") {
    if (status === "complete") return "已完成";
    if (status === "in_progress") return "进行中";
    return "尚未开始";
  }
  if (status === "complete") return "Complete";
  if (status === "in_progress") return "In progress";
  return "Not started";
}

export function completedStepCount(experiment: TextSignalExperiment): number {
  return experiment.steps?.filter((step) => step.done).length ?? 0;
}
