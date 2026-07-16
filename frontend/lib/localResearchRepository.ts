/**
 * LocalResearchRepository — Sprint 1 persistence via localStorage.
 * Demo MA Crossover remains catalog-backed; user research is local-only.
 */

import {
  CANONICAL_RESEARCH_ID,
  getMockResearchById,
  getMockResearchDetails,
} from "@/lib/mockResearchCatalog";
import {
  isEvidenceAvailableStatus,
  type CreateResearchInput,
  type ResearchRepository,
  type ResearchWorkspaceSnapshot,
} from "@/lib/researchRepository";
import {
  toResearchListItem,
  type ResearchDetail,
  type ResearchListItem,
} from "@/types/research";

export const RESEARCH_WORKSPACE_STORAGE_KEY = "quant.research.workspace.v1";

function emptySnapshot(): ResearchWorkspaceSnapshot {
  return {
    demoVisible: true,
    userResearch: [],
  };
}

function readSnapshot(): ResearchWorkspaceSnapshot {
  if (typeof window === "undefined") {
    return emptySnapshot();
  }
  try {
    const raw = window.localStorage.getItem(RESEARCH_WORKSPACE_STORAGE_KEY);
    if (!raw) {
      return emptySnapshot();
    }
    const parsed = JSON.parse(raw) as Partial<ResearchWorkspaceSnapshot>;
    return {
      demoVisible: parsed.demoVisible !== false,
      userResearch: Array.isArray(parsed.userResearch) ? parsed.userResearch : [],
    };
  } catch {
    return emptySnapshot();
  }
}

function writeSnapshot(snapshot: ResearchWorkspaceSnapshot): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(
      RESEARCH_WORKSPACE_STORAGE_KEY,
      JSON.stringify(snapshot)
    );
  } catch {
    // Ignore quota / private-mode failures; UI stays session-local.
  }
}

function buildUserResearch(input: CreateResearchInput): ResearchDetail {
  const now = new Date().toISOString();
  const id = `research-${Date.now().toString(36)}-${Math.random()
    .toString(36)
    .slice(2, 8)}`;
  const strategyName = "Moving Average Crossover";
  const tags = input.tags.map((tag) => tag.trim()).filter(Boolean);

  return {
    id,
    name: input.name.trim(),
    researchQuestion: input.researchQuestion.trim(),
    status: "Draft",
    currentStage: "Draft",
    confidenceScore: null,
    owner: input.owner.trim() || "Research Workspace",
    tags: tags.length ? tags : ["draft"],
    createdAt: now,
    updatedAt: now,
    experimentCount: 0,
    lastValidation: "No formal validation yet",
    currentRecommendation: "Define the first experiment before seeking evidence.",
    integrity: {
      dataStatus: "Not started",
      metricsStatus: "Not Calculated",
      validationStatus: "Not Started",
      evaluationStatus: "Not Available",
      publicityLabel: "Local research definition — execution uses the backend",
      explanatoryText:
        "This definition is stored in this browser. Calculated evidence comes from the real backend and is not stored as a completed result here.",
      evaluationPendingMessage: "Evaluation pending first validation evidence",
    },
    configuration: {
      symbol: input.symbol.trim().toUpperCase(),
      benchmark: `${input.benchmark.trim().toUpperCase()} Buy & Hold`,
      strategyName,
      parameterLines: [
        `Short Window: ${input.shortWindow}`,
        `Long Window: ${input.longWindow}`,
        `Transaction Cost: ${input.transactionCost}`,
        `History Window: ${input.startDate} → ${input.endDate}`,
      ],
      dataRequirements: [
        `Historical daily prices for ${input.symbol.trim().toUpperCase()}`,
        "Same-asset buy-and-hold benchmark over the identical history",
      ],
    },
    runConfiguration: {
      symbol: input.symbol.trim().toUpperCase(),
      benchmark: input.benchmark.trim().toUpperCase(),
      startDate: input.startDate,
      endDate: input.endDate,
      shortWindow: input.shortWindow,
      longWindow: input.longWindow,
      transactionCost: input.transactionCost,
      riskFreeRate: 0,
    },
    hypothesis: input.researchQuestion.trim(),
    researchObjective:
      "Execute the configured MA Crossover protocol and evaluate only backend-calculated evidence.",
    researchSummary:
      "Local research definition created from the MA Crossover template.",
    evidenceSummary: "No calculated evidence yet.",
    validationSummary: "Validation has not started.",
    keyStrengths: ["Research captured as a first-class workspace object"],
    knownWeaknesses: ["Sprint-1 local persistence only — not backend-backed"],
    openQuestions: [
      input.researchQuestion.trim() || "What evidence would falsify this research?",
    ],
    nextActions: [
      "Open the workspace and run the configured research execution",
      "Run validation before generating evaluation or Copilot interpretation",
    ],
    evidenceItems: [],
  };
}

function mergeList(snapshot: ResearchWorkspaceSnapshot): ResearchDetail[] {
  const demo = snapshot.demoVisible ? getMockResearchDetails() : [];
  const user = snapshot.userResearch.map((item) => ({
    ...item,
    tags: [...item.tags],
    keyStrengths: [...(item.keyStrengths ?? [])],
    knownWeaknesses: [...(item.knownWeaknesses ?? [])],
    openQuestions: [...(item.openQuestions ?? [])],
    nextActions: [...(item.nextActions ?? [])],
    evidenceItems: (item.evidenceItems ?? []).map((evidence) => ({ ...evidence })),
    integrity: { ...item.integrity },
    configuration: {
      ...item.configuration,
      parameterLines: [...(item.configuration.parameterLines ?? [])],
      dataRequirements: [...(item.configuration.dataRequirements ?? [])],
    },
    runConfiguration: item.runConfiguration
      ? { ...item.runConfiguration }
      : undefined,
  }));
  return [...demo, ...user];
}

export class LocalResearchRepository implements ResearchRepository {
  async list(): Promise<ResearchListItem[]> {
    return mergeList(readSnapshot()).map(toResearchListItem);
  }

  async getById(researchId: string): Promise<ResearchDetail | null> {
    if (researchId === CANONICAL_RESEARCH_ID) {
      const snapshot = readSnapshot();
      if (!snapshot.demoVisible) {
        return null;
      }
      return getMockResearchById(researchId);
    }
    return (
      mergeList(readSnapshot()).find((item) => item.id === researchId) ?? null
    );
  }

  async create(input: CreateResearchInput): Promise<ResearchDetail> {
    if (!input.name.trim()) {
      throw new Error("Research name is required.");
    }
    if (!input.researchQuestion.trim()) {
      throw new Error("Research question is required.");
    }
    if (!input.symbol.trim()) {
      throw new Error("Symbol is required.");
    }
    if (input.shortWindow <= 0) {
      throw new Error("Short MA window must be positive.");
    }
    if (input.longWindow <= input.shortWindow) {
      throw new Error("Long MA window must be greater than the short window.");
    }
    if (!input.startDate || !input.endDate || input.startDate >= input.endDate) {
      throw new Error("Start date must be before end date.");
    }
    if (input.transactionCost < 0) {
      throw new Error("Transaction cost cannot be negative.");
    }
    const created = buildUserResearch(input);
    const snapshot = readSnapshot();
    snapshot.userResearch = [created, ...snapshot.userResearch];
    writeSnapshot(snapshot);
    return created;
  }

  async archive(researchId: string): Promise<void> {
    const snapshot = readSnapshot();
    if (researchId === CANONICAL_RESEARCH_ID) {
      snapshot.demoVisible = false;
      writeSnapshot(snapshot);
      return;
    }
    snapshot.userResearch = snapshot.userResearch.map((item) =>
      item.id === researchId
        ? {
            ...item,
            status: "Archived",
            updatedAt: new Date().toISOString(),
            currentRecommendation: "Archived from Research List",
          }
        : item
    );
    writeSnapshot(snapshot);
  }

  async includeDemoResearch(): Promise<void> {
    const snapshot = readSnapshot();
    snapshot.demoVisible = true;
    writeSnapshot(snapshot);
  }

  async getSummary(): Promise<{
    total: number;
    defined: number;
    evidenceAvailable: number;
    reviewOrArchived: number;
  }> {
    const items = await this.list();
    return {
      total: items.length,
      defined: items.filter((item) => item.status === "Draft").length,
      evidenceAvailable: items.filter((item) =>
        isEvidenceAvailableStatus(item.status)
      ).length,
      reviewOrArchived: items.filter(
        (item) => item.status === "Review" || item.status === "Archived"
      ).length,
    };
  }
}

let defaultRepository: ResearchRepository | null = null;

export function getResearchRepository(): ResearchRepository {
  if (!defaultRepository) {
    defaultRepository = new LocalResearchRepository();
  }
  return defaultRepository;
}

/** Test helper — reset singleton between tests if needed. */
export function setResearchRepositoryForTests(
  repository: ResearchRepository | null
): void {
  defaultRepository = repository;
}
