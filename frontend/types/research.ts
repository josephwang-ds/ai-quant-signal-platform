/** Research List / Workspace 领域投影类型（前端 mock；后端接入后对齐 API）。 */

/** 列表与徽标使用的运营状态（产品投影，非 Ch3 权威状态机全集）。 */
export type ResearchLifecycleStatus =
  | "Draft"
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

export type ResearchListItem = {
  id: string;
  name: string;
  researchQuestion: string;
  status: ResearchLifecycleStatus;
  /** 0–100 置信度分数；null = 待 Research Execution Engine 计算 */
  confidenceScore: number | null;
  owner: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  experimentCount: number;
  lastValidation: string;
  currentRecommendation: string;
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
};

export const RESEARCH_LIFECYCLE_STATUSES: ResearchLifecycleStatus[] = [
  "Draft",
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
  "timeline",
  "files",
  "settings",
] as const;

export type ResearchWorkspaceSection = (typeof RESEARCH_WORKSPACE_SECTIONS)[number];

/** 将列表运营状态映射到 Ch3 进度阶段（无显式 currentStage 时的兜底）。 */
export function mapLifecycleStatusToProgressStage(
  status: ResearchLifecycleStatus
): ResearchProgressStage {
  switch (status) {
    case "Draft":
      return "Draft";
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
  };
}
