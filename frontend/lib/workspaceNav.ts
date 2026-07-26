/**
 * Global workspace navigation — keep the research spine visible and move
 * supporting utilities behind compact, collapsible groups.
 */

import type { TranslationKey } from "@/lib/i18n";

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

export const WORKSPACE_NAV_GROUPS: WorkspaceNavGroup[] = [
  {
    id: "research",
    labelKey: "navGroupResearch",
    items: [{ href: "/", labelKey: "navResearchWorkspace" }],
  },
  {
    id: "workbench",
    labelKey: "navGroupWorkbench",
    items: [
      { href: "/compare-models", labelKey: "navCompareModels" },
      { href: "/strategy-lab", labelKey: "navStrategyLab" },
    ],
  },
  {
    id: "supporting",
    labelKey: "navGroupSupporting",
    items: [
      { href: "/ai-insights", labelKey: "navAiInsights" },
      { href: "/data-center", labelKey: "navDataCenter" },
    ],
  },
];

export function isWorkspaceNavItemActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/" || pathname.startsWith("/research/");
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
