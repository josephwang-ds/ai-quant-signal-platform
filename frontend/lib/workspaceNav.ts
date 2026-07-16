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

/**
 * Global nav — Research is the product; other modules are supporting tools.
 * Routes are unchanged.
 */
export const WORKSPACE_NAV_GROUPS: WorkspaceNavGroup[] = [
  {
    id: "tools",
    labelKey: "navGroupTools",
    items: [
      { href: "/strategy-lab", labelKey: "navStrategyLab" },
      { href: "/comparison", labelKey: "navComparison" },
      { href: "/robustness", labelKey: "navRobustness" },
      { href: "/paper-trading", labelKey: "navPaperTrading" },
      { href: "/market-watch", labelKey: "navMarketWatch" },
    ],
  },
  {
    id: "archive",
    labelKey: "navGroupArchive",
    items: [
      { href: "/data-center", labelKey: "navDataCenter" },
      { href: "/experiments", labelKey: "navExperiments" },
    ],
  },
];

export function isWorkspaceNavItemActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/" || pathname.startsWith("/research/");
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
