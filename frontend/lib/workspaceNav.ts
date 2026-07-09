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

/** 顶栏只展示可用模块；开发中/未开始的入口保留在总览页。 */
export const WORKSPACE_NAV_GROUPS: WorkspaceNavGroup[] = [
  {
    id: "research",
    labelKey: "navGroupResearch",
    items: [
      { href: "/market-watch", labelKey: "navMarketWatch" },
      { href: "/strategy-lab", labelKey: "navStrategyLab" },
      { href: "/paper-trading", labelKey: "navPaperTrading" },
      { href: "/comparison", labelKey: "navComparison" },
      { href: "/robustness", labelKey: "navRobustness" },
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
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function isWorkspaceNavGroupActive(
  pathname: string,
  group: WorkspaceNavGroup
): boolean {
  return group.items.some((item) => isWorkspaceNavItemActive(pathname, item.href));
}
