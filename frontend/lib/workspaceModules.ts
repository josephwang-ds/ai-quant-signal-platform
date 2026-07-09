import type { TranslationKey } from "@/lib/i18n";

export type ModuleStatus = "active" | "planned" | "comingLater";

export type ModuleCategory = "core" | "data" | "model";

export type ModuleSkeletonKind = "planned" | "migrating";

export type WorkspaceModule = {
  id: string;
  href: string;
  titleKey: TranslationKey;
  overviewDescKey: TranslationKey;
  pageDescKey: TranslationKey;
  status: ModuleStatus;
  skeletonKind: ModuleSkeletonKind;
  category: ModuleCategory;
  legacyAnchor?: string;
};

export const WORKSPACE_MODULES: WorkspaceModule[] = [
  {
    id: "market-watch",
    href: "/market-watch",
    titleKey: "marketWatch",
    overviewDescKey: "moduleMarketWatchOverviewDesc",
    pageDescKey: "marketWatchDesc",
    status: "active",
    skeletonKind: "migrating",
    category: "core",
  },
  {
    id: "strategy-lab",
    href: "/strategy-lab",
    titleKey: "strategyLab",
    overviewDescKey: "moduleStrategyLabOverviewDesc",
    pageDescKey: "strategyLabDesc",
    status: "active",
    skeletonKind: "migrating",
    category: "core",
  },
  {
    id: "comparison",
    href: "/comparison",
    titleKey: "strategyComparison",
    overviewDescKey: "moduleComparisonOverviewDesc",
    pageDescKey: "strategyComparisonDesc",
    status: "active",
    skeletonKind: "migrating",
    category: "core",
  },
  {
    id: "robustness",
    href: "/robustness",
    titleKey: "robustnessChecks",
    overviewDescKey: "moduleRobustnessOverviewDesc",
    pageDescKey: "robustnessChecksDesc",
    status: "active",
    skeletonKind: "migrating",
    category: "core",
  },
  {
    id: "data-center",
    href: "/data-center",
    titleKey: "dataCenter",
    overviewDescKey: "moduleDataCenterOverviewDesc",
    pageDescKey: "dataCenterDesc",
    status: "active",
    skeletonKind: "planned",
    category: "data",
  },
  {
    id: "experiments",
    href: "/experiments",
    titleKey: "experiments",
    overviewDescKey: "moduleExperimentsOverviewDesc",
    pageDescKey: "experimentsDesc",
    status: "active",
    skeletonKind: "planned",
    category: "data",
  },
  {
    id: "research-notes",
    href: "/research-notes",
    titleKey: "researchNotes",
    overviewDescKey: "moduleResearchNotesOverviewDesc",
    pageDescKey: "researchNotesDesc",
    status: "planned",
    skeletonKind: "planned",
    category: "data",
  },
  {
    id: "model-lab",
    href: "/model-lab",
    titleKey: "modelLab",
    overviewDescKey: "moduleModelLabOverviewDesc",
    pageDescKey: "modelLabDesc",
    status: "comingLater",
    skeletonKind: "planned",
    category: "model",
  },
  {
    id: "ai-agent",
    href: "/ai-agent",
    titleKey: "aiResearchAgent",
    overviewDescKey: "moduleAiAgentOverviewDesc",
    pageDescKey: "aiResearchAgentDesc",
    status: "comingLater",
    skeletonKind: "planned",
    category: "model",
  },
];

export const MODULE_CATEGORIES: Array<{
  id: ModuleCategory;
  titleKey: TranslationKey;
  moduleIds: string[];
}> = [
  {
    id: "core",
    titleKey: "categoryCoreResearch",
    moduleIds: ["market-watch", "strategy-lab", "comparison", "robustness"],
  },
  {
    id: "data",
    titleKey: "categoryDataStorage",
    moduleIds: ["data-center", "experiments", "research-notes"],
  },
  {
    id: "model",
    titleKey: "categoryModelAi",
    moduleIds: ["model-lab", "ai-agent"],
  },
];

export function moduleStatusLabelKey(status: ModuleStatus): TranslationKey {
  switch (status) {
    case "active":
      return "statusActive";
    case "planned":
      return "statusPlanned";
    case "comingLater":
      return "statusComingLater";
  }
}

export function moduleSkeletonStatusKey(kind: ModuleSkeletonKind): TranslationKey {
  return kind === "migrating" ? "moduleMigratingStatus" : "modulePlannedStatus";
}

export function moduleStatusBadgeVariant(
  status: ModuleStatus
): "success" | "info" | "neutral" {
  switch (status) {
    case "active":
      return "success";
    case "planned":
      return "info";
    case "comingLater":
      return "neutral";
  }
}
