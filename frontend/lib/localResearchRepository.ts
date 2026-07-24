/**
 * LocalResearchRepository — Sprint 1 persistence via localStorage.
 * Demo catalog remains catalog-backed; user research is local-only and research-first.
 */

import {
  CANONICAL_RESEARCH_ID,
  CANONICAL_FACTOR_RESEARCH_ID,
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
  isFactorRunConfiguration,
  toResearchListItem,
  type ResearchDetail,
  type ResearchListItem,
} from "@/types/research";

export const RESEARCH_WORKSPACE_STORAGE_KEY = "quant.research.workspace.v1";

const DEMO_RESEARCH_IDS = new Set([
  CANONICAL_RESEARCH_ID,
  CANONICAL_FACTOR_RESEARCH_ID,
]);

function emptySnapshot(): ResearchWorkspaceSnapshot {
  return {
    demoVisible: true,
    archivedDemoIds: [],
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
    const parsed = JSON.parse(raw) as Partial<ResearchWorkspaceSnapshot> & {
      archivedDemoIds?: string[];
    };
    const archivedDemoIds = Array.isArray(parsed.archivedDemoIds)
      ? parsed.archivedDemoIds.filter((id): id is string => typeof id === "string")
      : [];
    return {
      demoVisible: parsed.demoVisible !== false,
      archivedDemoIds,
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
  const runConfiguration = input.runConfiguration
    ? { ...input.runConfiguration }
    : undefined;
  const isFactor = isFactorRunConfiguration(runConfiguration);

  return {
    id,
    name: input.name.trim(),
    researchQuestion,
    status: "Draft",
    currentStage: "Draft",
    confidenceScore: null,
    owner: input.owner?.trim() || "Research Workspace",
    tags: tags.length
      ? tags
      : isFactor
        ? ["draft", "cross-sectional-factor"]
        : ["draft"],
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
    configuration: isFactor
      ? {
          symbol: "US Sector ETFs",
          benchmark: "Equal-weight quantile long–short (Q5−Q1)",
          strategyName: "Cross-Sectional Factor Validation",
          parameterLines: [
            `Universe: ${runConfiguration.universeId}`,
            `Factor: ${runConfiguration.factorId}`,
            `Rebalance: ${runConfiguration.rebalanceFrequency}`,
            `Holding Period: ${runConfiguration.holdingPeriodMonths} month(s)`,
            `Transaction cost ${runConfiguration.transactionCost}`,
          ],
          dataRequirements: [
            `Universe preset ${runConfiguration.universeId}`,
            "Daily OHLCV for each universe member",
          ],
        }
      : {
          symbol: runConfiguration && "symbol" in runConfiguration
            ? runConfiguration.symbol
            : "—",
          benchmark: runConfiguration && "benchmark" in runConfiguration
            ? runConfiguration.benchmark
            : "—",
          strategyName: runConfiguration
            ? "Moving Average Crossover"
            : "Not configured",
          parameterLines: runConfiguration && "shortWindow" in runConfiguration
            ? [
                `MA ${runConfiguration.shortWindow}/${runConfiguration.longWindow}`,
                `Transaction cost ${runConfiguration.transactionCost}`,
              ]
            : [],
          dataRequirements: runConfiguration && "symbol" in runConfiguration
            ? [
                `${runConfiguration.symbol} adjusted daily prices`,
                `${runConfiguration.benchmark} benchmark prices`,
              ]
            : [
                "Define datasets and experiment protocols inside the research workspace",
              ],
        },
    runConfiguration,
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
  const archived = new Set(snapshot.archivedDemoIds);
  const demosHidden = snapshot.demoVisible === false;
  const demo = demosHidden
    ? []
    : getMockResearchDetails().filter((item) => !archived.has(item.id));
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
    if (DEMO_RESEARCH_IDS.has(researchId)) {
      const snapshot = readSnapshot();
      if (snapshot.demoVisible === false) {
        return null;
      }
      if (snapshot.archivedDemoIds.includes(researchId)) {
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
    if (DEMO_RESEARCH_IDS.has(researchId)) {
      if (!snapshot.archivedDemoIds.includes(researchId)) {
        snapshot.archivedDemoIds = [...snapshot.archivedDemoIds, researchId];
      }
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

  async deletePermanently(researchId: string): Promise<void> {
    if (DEMO_RESEARCH_IDS.has(researchId)) {
      throw new Error("The built-in demo research cannot be permanently deleted.");
    }
    const snapshot = readSnapshot();
    snapshot.userResearch = snapshot.userResearch.filter(
      (item) => item.id !== researchId
    );
    writeSnapshot(snapshot);
  }

  async includeDemoResearch(): Promise<void> {
    const snapshot = readSnapshot();
    snapshot.demoVisible = true;
    snapshot.archivedDemoIds = [];
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
