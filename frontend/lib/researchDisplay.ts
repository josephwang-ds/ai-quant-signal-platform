import type { Language } from "@/lib/i18n";
import type { ExperimentStatus, ExperimentType, ValidationReadiness } from "@/types/experiment";
import type { ResearchLifecycleStatus } from "@/types/research";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";

const RESEARCH_STATUS_ZH: Record<ResearchLifecycleStatus, string> = {
  Draft: "草稿",
  "Data Integration": "数据接入",
  Running: "运行中",
  Review: "待复核",
  Validated: "已验证",
  "Paper Trading": "模拟试盘",
  Monitoring: "监控中",
  Archived: "已归档",
};

const EXPERIMENT_STATUS_ZH: Record<ExperimentStatus, string> = {
  Designed: "已设计",
  Approved: "已批准",
  Running: "运行中",
  Completed: "已完成",
  Failed: "失败",
  Invalidated: "已作废",
};

const EXPERIMENT_TYPE_ZH: Record<ExperimentType, string> = {
  Backtest: "回测",
  "Parameter Test": "参数测试",
  "Feature Test": "特征测试",
  "Regime Test": "市场状态测试",
  "Cost Test": "成本测试",
  "Model Comparison": "模型对比",
};

const READINESS_ZH: Record<ValidationReadiness, string> = {
  not_ready: "未就绪",
  partial: "部分就绪",
  ready: "已就绪",
  blocked: "已阻塞",
};

export function researchStatusLabel(status: ResearchLifecycleStatus, language: Language) {
  return language === "zh" ? RESEARCH_STATUS_ZH[status] : status;
}

export function experimentStatusLabel(status: ExperimentStatus, language: Language) {
  return language === "zh" ? EXPERIMENT_STATUS_ZH[status] : status;
}

export function experimentTypeLabel(type: ExperimentType, language: Language) {
  return language === "zh" ? EXPERIMENT_TYPE_ZH[type] : type;
}

export function validationReadinessLabel(
  readiness: ValidationReadiness,
  language: Language
) {
  return language === "zh" ? READINESS_ZH[readiness] : readiness;
}

export function ownerLabel(owner: string, language: Language) {
  return language === "zh" && owner === "Research Workspace" ? "研究工作区" : owner;
}

export function benchmarkLabel(benchmark: string, language: Language) {
  return language === "zh"
    ? benchmark.replace("Buy & Hold", "买入并持有")
    : benchmark;
}

export function evidenceStatusLabel(status: string, language: Language) {
  if (language !== "zh") return status;
  const labels: Record<string, string> = {
    "Not Started": "未开始",
    "Partial — Historical & Benchmark only": "部分完成——仅历史回测与基准对比",
    Completed: "已完成",
    "Awaiting Data": "等待数据",
    "Awaiting Engine": "等待计算引擎",
  };
  return labels[status] ?? status;
}

export function strategyLabel(value: string, language: Language) {
  return language === "zh" && value === "Moving Average Crossover"
    ? "移动平均线交叉"
    : value;
}

export function parameterLineLabel(value: string, language: Language) {
  if (language !== "zh") return value;
  return value
    .replace("Short Window", "短周期")
    .replace("Long Window", "长周期")
    .replace("Transaction Cost", "交易成本")
    .replace("Start Date", "开始日期")
    .replace("End Date", "结束日期");
}

export function researchNameLabel(id: string, value: string, language: Language) {
  return language === "zh" && id === CANONICAL_RESEARCH_ID
    ? "趋势跟踪研究"
    : value;
}

export function researchQuestionLabel(
  id: string,
  value: string,
  language: Language
) {
  return language === "zh" && id === CANONICAL_RESEARCH_ID
    ? "均线策略在计入交易成本后，能否持续跑赢买入并持有？"
    : value;
}

export function timelineEventTitleLabel(value: string, language: Language) {
  if (language !== "zh") return value;
  const labels: Record<string, string> = {
    "Research Definition Created": "已创建研究定义",
    "Research Methodology Documented": "已记录研究方法",
    "Real Data Integration Planned": "已规划真实数据接入",
  };
  return labels[value] ?? value;
}

export function timelineEventSummaryLabel(value: string, language: Language) {
  if (language !== "zh") return value;
  const labels: Record<string, string> = {
    "Canonical Trend Following Study defined for the public Research Hub.":
      "已为公开研究工作区定义标准趋势跟踪案例。",
    "MA20/MA60, lag-1 position, 0.001 cost, SPY vs buy-and-hold protocol documented as design notes.":
      "已将 MA20/MA60、滞后一日持仓、0.001 交易成本及 SPY 买入并持有基准记录为研究设计。",
    "Market-derived evidence deferred to the Research Execution Engine (PR-008B+).":
      "市场数据证据由研究执行引擎计算，在此之前不展示虚构指标。",
  };
  return labels[value] ?? value;
}

export function timelineEventKindLabel(value: string, language: Language) {
  if (language !== "zh") return value;
  const labels: Record<string, string> = {
    stage_change: "阶段变更",
    notebook_entry: "研究记录",
    experiment: "实验",
    validation: "验证",
  };
  return labels[value] ?? value;
}

export function formatResearchTimestamp(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function localizeEvidenceNote(value: string, language: Language): string {
  if (language !== "zh") return value;
  const known: Record<string, string> = {
    "Yahoo Finance / yfinance is suitable for research and portfolio demos only — not an exchange-grade production feed.":
      "Yahoo Finance / yfinance 为研究级数据源，不是交易所级行情。",
    "Provider timeout is enforced via yfinance download(timeout=…).":
      "数据下载已启用超时保护。",
    "Yahoo prices use yfinance auto_adjust (auto_adjust).":
      "价格使用 yfinance 自动复权口径。",
    "The strategy is run once on full history, then valid return rows are sliced at split_date. The first OOS row therefore preserves its full-run position, turnover, and transaction cost against the prior in-sample row.":
      "策略先在完整历史区间运行，再按切分日期划分有效收益；首个样本外观测保留与上一样本内观测连续的仓位、换手和交易成本。",
  };
  if (known[value]) return known[value];

  const cutoff = value.match(
    /^Open-ended request clipped to completed daily bars only \(exclusive cutoff (\d{4}-\d{2}-\d{2}) America\/New_York\)\.$/
  );
  if (cutoff) {
    return `已自动排除尚未收盘的当日行情，数据截止 ${cutoff[1]}（纽约市场日界线）。`;
  }

  const dropped = value.match(
    /^Dropped (\d+) incomplete Yahoo Finance bar\(s\) with missing OHLC before validation\.$/
  );
  if (dropped) {
    return `验证前已排除 ${dropped[1]} 条 OHLC 不完整的 Yahoo Finance 记录。`;
  }
  return value;
}
