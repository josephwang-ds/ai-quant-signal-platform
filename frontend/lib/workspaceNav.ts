/**
 * Global nav — Research Library is the entry; tools are secondary.
 * Lifecycle stages live inside the research workspace, not as global top items.
 * Routes remain reachable for backward compatibility.
 */

import type { TranslationKey } from "@/lib/i18n";

export type WorkspaceNavItem = {
  href: string;
  labelKey: TranslationKey;
};

export type WorkspaceNavGroup = {
  id: string;
  labelKey: TranslationKey;
  items: WorkspaceNavItem[];
};

export const WORKSPACE_NAV_GROUPS: WorkspaceNavGroup[] = [
  {
    id: "tools",
    labelKey: "navGroupTools",
    items: [
      { href: "/strategy-lab", labelKey: "navStrategyLab" },
      { href: "/comparison", labelKey: "navComparison" },
      { href: "/market-watch", labelKey: "navMarketWatch" },
    ],
  },
  {
    id: "supporting",
    labelKey: "navGroupSupporting",
    items: [
      { href: "/data-center", labelKey: "navDataCenter" },
      { href: "/experiments", labelKey: "navExperiments" },
      { href: "/overview", labelKey: "navModuleDirectory" },
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
  return pathname.startsWith(href);
}

export function isWorkspaceNavGroupActive(
  pathname: string,
  group: WorkspaceNavGroup
): boolean {
  return group.items.some((item) => isWorkspaceNavItemActive(pathname, item.href));
}
