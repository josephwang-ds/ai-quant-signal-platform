/**
 * Experiment 筛选、校验、生命周期与本地构造。
 *
 * TODO(backend): 替换为 Experiment Application 用例与持久化端口。
 * TODO(api): 状态迁移必须经治理工作流，禁止 UI 静默跃迁。
 */

import type {
  ExperimentComposerValues,
  ExperimentFilters,
  ExperimentProgressStage,
  ExperimentStatus,
  ResearchExperiment,
} from "@/types/experiment";
import {
  EMPTY_EXPERIMENT_METRICS,
  EXPERIMENT_PROGRESS_STAGES,
  EXPERIMENT_TYPES,
} from "@/types/experiment";
import type { NotebookEntry, ResearchTimelineEvent } from "@/types/notebook";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
} from "@/lib/formatters";

export type LifecycleStepState = "completed" | "current" | "upcoming" | "terminal";

export function isActiveExperimentStatus(status: ExperimentStatus): boolean {
  return status === "Designed" || status === "Approved" || status === "Running";
}

export function countActiveExperiments(experiments: ResearchExperiment[]): number {
  return experiments.filter((item) => isActiveExperimentStatus(item.status)).length;
}

export function getExperimentLifecycleStepState(
  stage: ExperimentProgressStage,
  status: ExperimentStatus
): LifecycleStepState {
  if (status === "Failed" || status === "Invalidated") {
    if (stage === "Designed") {
      return "completed";
    }
    return "upcoming";
  }

  const stageIndex = EXPERIMENT_PROGRESS_STAGES.indexOf(stage);
  const currentIndex = EXPERIMENT_PROGRESS_STAGES.indexOf(
    status as ExperimentProgressStage
  );

  if (stageIndex < 0 || currentIndex < 0) {
    return "upcoming";
  }
  if (stageIndex < currentIndex) {
    return "completed";
  }
  if (stageIndex === currentIndex) {
    return "current";
  }
  return "upcoming";
}

export function filterAndSortExperiments(
  experiments: ResearchExperiment[],
  filters: ExperimentFilters
): ResearchExperiment[] {
  const query = filters.query.trim().toLowerCase();

  const filtered = experiments.filter((item) => {
    if (filters.status !== "all" && item.status !== filters.status) {
      return false;
    }
    if (
      filters.experimentType !== "all" &&
      item.experimentType !== filters.experimentType
    ) {
      return false;
    }
    if (!query) {
      return true;
    }
    const haystack = [
      item.name,
      item.hypothesis,
      item.datasetOrSymbol,
      item.benchmark,
      item.resultSummary,
      ...item.parameters.map((parameter) => `${parameter.key} ${parameter.value}`),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  const sorted = [...filtered];
  sorted.sort((a, b) => {
    switch (filters.sort) {
      case "created":
        return Date.parse(b.createdAt) - Date.parse(a.createdAt);
      case "result": {
        const aSharpe = a.metrics.sharpe ?? Number.NEGATIVE_INFINITY;
        const bSharpe = b.metrics.sharpe ?? Number.NEGATIVE_INFINITY;
        return bSharpe - aSharpe;
      }
      case "updated":
      default:
        return Date.parse(b.updatedAt) - Date.parse(a.updatedAt);
    }
  });

  return sorted;
}

export type ExperimentComposerErrors = Partial<
  Record<
    | "name"
    | "hypothesis"
    | "experimentType"
    | "datasetOrSymbol"
    | "startDate"
    | "endDate"
    | "dateRange"
    | "successCriteria"
    | "falsificationCondition",
    string
  >
>;

export function validateExperimentComposer(
  values: ExperimentComposerValues,
  messages: {
    nameRequired: string;
    hypothesisRequired: string;
    typeRequired: string;
    datasetRequired: string;
    startRequired: string;
    endRequired: string;
    dateRangeInvalid: string;
    successRequired: string;
    falsificationRequired: string;
  }
): ExperimentComposerErrors {
  const errors: ExperimentComposerErrors = {};

  if (!values.name.trim()) {
    errors.name = messages.nameRequired;
  }
  if (!values.hypothesis.trim()) {
    errors.hypothesis = messages.hypothesisRequired;
  }
  if (
    !values.experimentType ||
    !EXPERIMENT_TYPES.includes(values.experimentType)
  ) {
    errors.experimentType = messages.typeRequired;
  }
  if (!values.datasetOrSymbol.trim()) {
    errors.datasetOrSymbol = messages.datasetRequired;
  }
  if (!values.startDate) {
    errors.startDate = messages.startRequired;
  }
  if (!values.endDate) {
    errors.endDate = messages.endRequired;
  }
  if (values.startDate && values.endDate) {
    const start = Date.parse(values.startDate);
    const end = Date.parse(values.endDate);
    if (Number.isNaN(start) || Number.isNaN(end) || start > end) {
      errors.dateRange = messages.dateRangeInvalid;
    }
  }
  if (!values.successCriteria.trim()) {
    errors.successCriteria = messages.successRequired;
  }
  if (!values.falsificationCondition.trim()) {
    errors.falsificationCondition = messages.falsificationRequired;
  }

  return errors;
}

export function hasExperimentComposerErrors(
  errors: ExperimentComposerErrors
): boolean {
  return Object.keys(errors).length > 0;
}

export function parseParametersInput(value: string): ResearchExperiment["parameters"] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const separator = line.includes("=") ? "=" : ":";
      const [key, ...rest] = line.split(separator);
      return {
        key: (key ?? "").trim() || "param",
        value: rest.join(separator).trim() || line,
      };
    });
}

export function createLocalExperiment(input: {
  researchId: string;
  owner: string;
  values: ExperimentComposerValues;
  now?: string;
}): ResearchExperiment {
  const now = input.now ?? new Date().toISOString();
  return {
    id: `exp-local-${input.researchId}-${Date.now()}`,
    researchId: input.researchId,
    name: input.values.name.trim(),
    hypothesis: input.values.hypothesis.trim(),
    status: "Designed",
    experimentType: input.values.experimentType as ResearchExperiment["experimentType"],
    datasetOrSymbol: input.values.datasetOrSymbol.trim(),
    startDate: input.values.startDate,
    endDate: input.values.endDate,
    benchmark: input.values.benchmark.trim() || "Buy & hold",
    parameters: parseParametersInput(input.values.parameters),
    successCriteria: input.values.successCriteria.trim(),
    falsificationCondition: input.values.falsificationCondition.trim(),
    notes: input.values.notes.trim(),
    owner: input.owner,
    createdAt: now,
    updatedAt: now,
    resultSummary: "Not run — Designed only. No execution in this mock.",
    metrics: { ...EMPTY_EXPERIMENT_METRICS },
    linkedNotebookEntryIds: [],
    relatedEvidenceIds: [],
    validationReadiness: "not_ready",
  };
}

/**
 * 由本地 ExperimentDesigned 派生 Notebook Decision 条目。
 * TODO(api): Application 用例同时写入 Notebook 聚合。
 */
export function createNotebookEntryFromExperiment(
  experiment: ResearchExperiment
): NotebookEntry {
  return {
    id: `nb-exp-${experiment.id}`,
    researchId: experiment.researchId,
    entryType: "Decision",
    title: `Experiment designed: ${experiment.name}`,
    body: `## ExperimentDesigned\n\n- Type: **${experiment.experimentType}**\n- Dataset: \`${experiment.datasetOrSymbol}\`\n- Window: ${experiment.startDate} → ${experiment.endDate}\n\n**Success:** ${experiment.successCriteria}\n\n**Falsify if:** ${experiment.falsificationCondition}`,
    author: experiment.owner,
    createdAt: experiment.createdAt,
    tags: ["experiment", "designed"],
    relatedArtifact: {
      id: experiment.id,
      label: experiment.name,
      kind: "experiment",
    },
  };
}

/**
 * 由本地 ExperimentDesigned 派生 Timeline 事件。
 * TODO(api): 发布 Research 上下文领域事件。
 */
export function createTimelineEventFromExperiment(
  experiment: ResearchExperiment
): ResearchTimelineEvent {
  return {
    id: `tl-exp-${experiment.id}`,
    researchId: experiment.researchId,
    occurredAt: experiment.createdAt,
    title: `ExperimentDesigned: ${experiment.name}`,
    summary: `${experiment.experimentType} on ${experiment.datasetOrSymbol} (${experiment.startDate} → ${experiment.endDate})`,
    kind: "experiment",
    sourceEntryId: experiment.id,
  };
}

/** Pending / unavailable metric cells — never invent numbers. */
export const METRIC_NOT_CALCULATED = "Not calculated";

export function formatMetricValue(
  value: number | null,
  kind: keyof ResearchExperiment["metrics"]
): string {
  if (value === null || Number.isNaN(value)) {
    return METRIC_NOT_CALCULATED;
  }
  switch (kind) {
    case "sharpe":
      return formatMetricSharpe(value);
    case "cagr":
    case "maxDrawdown":
    case "volatility":
    case "winRate":
      return formatMetricPercent(value);
    case "tradeCount":
      return formatMetricTrades(value);
    case "totalTransactionCost":
      return `${value.toFixed(1)} bps`;
    default:
      return String(value);
  }
}
