/** Research List / Workspace 领域投影类型（前端；后端接入后对齐 API）。 */

/** 列表与徽标使用的运营状态（产品投影；含 authenticity “Data Integration”). */
export type ResearchLifecycleStatus =
  | "Draft"
  | "Data Integration"
  | "Running"
  | "Review"
  | "Validated"
  | "Paper Trading"
  | "Monitoring"
  | "Archived";

/**
 * Research 聚合进度阶段（对齐 Architecture Bible Ch3）。
 * LifecycleProgress 组件使用此序列。
 */
export type ResearchProgressStage =
  | "Draft"
  | "Planning"
  | "Running"
  | "Synthesizing"
  | "Reviewed"
  | "Closed";

export type EvidenceItemStatus = "completed" | "in_progress" | "pending" | "blocked";

export type ResearchEvidenceItem = {
  id: string;
  label: string;
  status: EvidenceItemStatus;
  result: string;
};

export type ResearchIntegrityDisplay = {
  dataStatus: string;
  metricsStatus: string;
  validationStatus: string;
  evaluationStatus: string;
  publicityLabel: string;
  explanatoryText: string;
  evaluationPendingMessage: string;
};

export type ResearchConfigurationDisplay = {
  symbol: string;
  benchmark: string;
  strategyName: string;
  parameterLines: string[];
  dataRequirements: string[];
};

/** Structured inputs for the one supported executable template: MA Crossover. */
export type ResearchRunConfiguration = {
  symbol: string;
  benchmark: string;
  startDate: string;
  endDate: string | null;
  shortWindow: number;
  longWindow: number;
  transactionCost: number;
  riskFreeRate: number;
};

export type ResearchListItem = {
  id: string;
  name: string;
  researchQuestion: string;
  status: ResearchLifecycleStatus;
  /** null until evaluation evidence exists — never invent a score */
  confidenceScore: number | null;
  owner: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  experimentCount: number;
  lastValidation: string;
  currentRecommendation: string;
  integrity: ResearchIntegrityDisplay;
  configuration: ResearchConfigurationDisplay;
};

export type ResearchDetail = ResearchListItem & {
  /** Ch3 进度阶段（驱动 LifecycleProgress） */
  currentStage: ResearchProgressStage;
  hypothesis: string;
  researchObjective: string;
  researchSummary: string;
  evidenceSummary: string;
  validationSummary: string;
  keyStrengths: string[];
  knownWeaknesses: string[];
  openQuestions: string[];
  nextActions: string[];
  evidenceItems: ResearchEvidenceItem[];
  /** Present when this definition can use the real execution/validation APIs. */
  runConfiguration?: ResearchRunConfiguration;
};

export const RESEARCH_LIFECYCLE_STATUSES: ResearchLifecycleStatus[] = [
  "Draft",
  "Data Integration",
  "Running",
  "Review",
  "Validated",
  "Paper Trading",
  "Monitoring",
  "Archived",
];

export const RESEARCH_PROGRESS_STAGES: ResearchProgressStage[] = [
  "Draft",
  "Planning",
  "Running",
  "Synthesizing",
  "Reviewed",
  "Closed",
];

export const RESEARCH_WORKSPACE_SECTIONS = [
  "overview",
  "notebook",
  "experiments",
  "validation",
  "evaluation",
  "copilot",
  "timeline",
  "files",
  "settings",
] as const;

export type ResearchWorkspaceSection = (typeof RESEARCH_WORKSPACE_SECTIONS)[number];

/** Primary Research IA sidebar (Evidence merges validation + evaluation content). */
export const RESEARCH_WORKSPACE_PRIMARY_SECTIONS: ResearchWorkspaceSection[] = [
  "overview",
  "experiments",
  "validation",
  "notebook",
  "settings",
];

/** Supporting tools kept for URL compatibility — not the product spine. */
export const RESEARCH_WORKSPACE_TOOL_SECTIONS: ResearchWorkspaceSection[] = [
  "copilot",
  "timeline",
  "files",
];

/** 将列表运营状态映射到 Ch3 进度阶段（无显式 currentStage 时的兜底）。 */
export function mapLifecycleStatusToProgressStage(
  status: ResearchLifecycleStatus
): ResearchProgressStage {
  switch (status) {
    case "Draft":
      return "Draft";
    case "Data Integration":
      return "Planning";
    case "Running":
      return "Running";
    case "Review":
      return "Reviewed";
    case "Validated":
      return "Reviewed";
    case "Paper Trading":
    case "Monitoring":
    case "Archived":
      return "Closed";
    default:
      return "Draft";
  }
}

export function toResearchListItem(detail: ResearchDetail): ResearchListItem {
  return {
    id: detail.id,
    name: detail.name,
    researchQuestion: detail.researchQuestion,
    status: detail.status,
    confidenceScore: detail.confidenceScore,
    owner: detail.owner,
    tags: [...detail.tags],
    createdAt: detail.createdAt,
    updatedAt: detail.updatedAt,
    experimentCount: detail.experimentCount,
    lastValidation: detail.lastValidation,
    currentRecommendation: detail.currentRecommendation,
    integrity: { ...detail.integrity },
    configuration: {
      ...detail.configuration,
      parameterLines: [...detail.configuration.parameterLines],
      dataRequirements: [...detail.configuration.dataRequirements],
    },
  };
}
