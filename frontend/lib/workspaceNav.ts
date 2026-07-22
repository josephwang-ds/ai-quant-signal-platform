/**
 * Global workspace navigation — primary modules always visible.
 * Archive remains a secondary, optionally collapsed group.
 */

import type { TranslationKey } from "@/lib/i18n";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";

export type WorkspaceNavItem = {
  href: string;
  labelKey: TranslationKey;
  /** Flagship module — optional visual emphasis in SideNav. */
  featured?: boolean;
};

export type WorkspaceNavGroup = {
  id: string;
  labelKey: TranslationKey;
  items: WorkspaceNavItem[];
  /** When true, SideNav may render as a collapsed <details>. */
  collapsible?: boolean;
};

export const CURRENT_STUDY_HREF = `/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}`;

export const WORKSPACE_NAV_GROUPS: WorkspaceNavGroup[] = [
  {
    id: "overview",
    labelKey: "navGroupOverview",
    items: [{ href: "/overview", labelKey: "navDashboard" }],
  },
  {
    id: "research",
    labelKey: "navGroupResearch",
    items: [
      { href: "/", labelKey: "navResearchWorkspace" },
      { href: CURRENT_STUDY_HREF, labelKey: "navCurrentResearch" },
    ],
  },
  {
    id: "analyze",
    labelKey: "navGroupAnalyze",
    items: [
      { href: "/market-watch", labelKey: "navMarketWatch" },
      { href: "/ai-insights", labelKey: "navAiInsights" },
      { href: "/strategy-lab", labelKey: "navStrategyLab" },
      { href: "/compare-models", labelKey: "navCompareModels", featured: true },
      { href: "/robustness", labelKey: "navPerformanceReview" },
      { href: "/risk-gate-review", labelKey: "navRiskReview" },
      { href: "/paper-trading", labelKey: "navPaperTrading" },
    ],
  },
  {
    id: "archive",
    labelKey: "navGroupArchive",
    collapsible: true,
    items: [
      { href: "/data-center", labelKey: "navDataCenter" },
      { href: "/experiments", labelKey: "navExperiments" },
    ],
  },
];

export function isWorkspaceNavItemActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }
  if (href === "/overview") {
    return pathname === "/overview";
  }
  if (href.startsWith("/research/")) {
    return pathname.startsWith("/research/");
  }
  return pathname.startsWith(href);
}

export function isWorkspaceNavGroupActive(
  pathname: string,
  group: WorkspaceNavGroup
): boolean {
  return group.items.some((item) => isWorkspaceNavItemActive(pathname, item.href));
}
