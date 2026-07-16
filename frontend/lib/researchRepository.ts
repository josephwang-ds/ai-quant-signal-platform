/**
 * Research persistence port — UI depends on this, not localStorage directly.
 * Future backend: swap LocalResearchRepository for ApiResearchRepository.
 */

import type { ResearchDetail, ResearchListItem, ResearchLifecycleStatus } from "@/types/research";

export type CreateResearchInput = {
  name: string;
  researchQuestion: string;
  symbol: string;
  benchmark: string;
  startDate: string;
  endDate: string;
  shortWindow: number;
  longWindow: number;
  transactionCost: number;
  tags: string[];
  owner: string;
};

export type ResearchWorkspaceSnapshot = {
  demoVisible: boolean;
  userResearch: ResearchDetail[];
};

export interface ResearchRepository {
  list(): Promise<ResearchListItem[]>;
  getById(researchId: string): Promise<ResearchDetail | null>;
  create(input: CreateResearchInput): Promise<ResearchDetail>;
  archive(researchId: string): Promise<void>;
  includeDemoResearch(): Promise<void>;
  getSummary(): Promise<{
    total: number;
    defined: number;
    evidenceAvailable: number;
    reviewOrArchived: number;
  }>;
}

export function isCompletedStatus(status: ResearchLifecycleStatus): boolean {
  return (
    status === "Validated" ||
    status === "Review" ||
    status === "Paper Trading" ||
    status === "Monitoring"
  );
}

export function isRunningStatus(status: ResearchLifecycleStatus): boolean {
  return status === "Running" || status === "Data Integration";
}

export function isEvidenceAvailableStatus(
  status: ResearchLifecycleStatus
): boolean {
  return (
    isRunningStatus(status) ||
    status === "Validated" ||
    status === "Paper Trading" ||
    status === "Monitoring"
  );
}
