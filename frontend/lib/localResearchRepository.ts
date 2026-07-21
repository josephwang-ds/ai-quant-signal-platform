/**
 * LocalResearchRepository — Sprint 1 persistence via localStorage.
 * Demo catalog remains catalog-backed; user research is local-only and research-first.
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
  const tags = input.tags.map((tag) => tag.trim()).filter(Boolean);
  const hypothesis = input.hypothesis.trim();
  const researchQuestion = input.researchQuestion.trim();

  return {
    id,
    name: input.name.trim(),
    researchQuestion,
    status: "Draft",
    currentStage: "Draft",
    confidenceScore: null,
    owner: input.owner?.trim() || "Research Workspace",
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
      publicityLabel: "Local research definition — experiments and execution come next",
      explanatoryText:
        "This research question is stored in this browser. Datasets, experiments, and calculated evidence are added inside the workspace — never invented on create.",
      evaluationPendingMessage: "Evaluation pending first validation evidence",
    },
    configuration: {
      symbol: "—",
      benchmark: "—",
      strategyName: "Not configured",
      parameterLines: [],
      dataRequirements: [
        "Define datasets and experiment protocols inside the research workspace",
      ],
    },
    hypothesis,
    researchObjective: hypothesis || researchQuestion,
    researchSummary:
      "Local research created as a research question. Experiments are designed inside the workspace.",
    evidenceSummary: "No calculated evidence yet.",
    validationSummary: "Validation has not started.",
    keyStrengths: ["Research captured as a first-class question-led workspace object"],
    knownWeaknesses: ["Sprint-1 local persistence only — not backend-backed"],
    openQuestions: [
      researchQuestion || "What evidence would falsify this research?",
    ],
    nextActions: [
      "Open the workspace and design the first experiment",
      "Attach datasets and run protocols before seeking evidence",
    ],
    evidenceItems: [],
  };
}

function mergeList(snapshot: ResearchWorkspaceSnapshot): ResearchDetail[] {
  const demo = snapshot.demoVisible ? getMockResearchDetails() : [];
  const user = snapshot.userResearch.map((item) => ({
    ...item,
    tags: [...item.tags],
    evidenceSummary: item.evidenceSummary ?? "No calculated evidence yet.",
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
    if (!input.hypothesis.trim()) {
      throw new Error("Hypothesis is required.");
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
