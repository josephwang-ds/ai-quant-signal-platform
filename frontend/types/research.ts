/** Research List 领域投影类型（前端 mock；后端接入后对齐 API）。 */

export type ResearchLifecycleStatus =
  | "Draft"
  | "Running"
  | "Review"
  | "Validated"
  | "Paper Trading"
  | "Monitoring"
  | "Archived";

export type ResearchListItem = {
  id: string;
  name: string;
  researchQuestion: string;
  status: ResearchLifecycleStatus;
  /** 0–100 置信度分数 */
  confidenceScore: number;
  owner: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  experimentCount: number;
  lastValidation: string;
  currentRecommendation: string;
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
