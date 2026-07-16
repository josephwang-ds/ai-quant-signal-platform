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
    ? "均线交叉研究"
    : value;
}

export function researchQuestionLabel(
  id: string,
  value: string,
  language: Language
) {
  return language === "zh" && id === CANONICAL_RESEARCH_ID
    ? "在计入交易成本后，MA20/MA60 能否长期跑赢 SPY 买入并持有基准？"
    : value;
}
