/**
 * Phase 4.6A navigation — Research Library first, Engine secondary.
 */

import type { TranslationKey } from "@/lib/i18n";
import { PRODUCT_REPO_URL } from "@/lib/productIdentity";
import { ENGINE_STAGES } from "@/lib/platformArchitecture";

export type WorkspaceNavItem = {
  href: string;
  labelKey: TranslationKey;
  /** Flagship module — optional visual emphasis in SideNav. */
  featured?: boolean;
  /** Open in a new tab (documentation). */
  external?: boolean;
};

export type WorkspaceNavGroup = {
  id: string;
  labelKey: TranslationKey;
  items: WorkspaceNavItem[];
  /** When true, SideNav may render as a collapsed <details>. */
  collapsible?: boolean;
};

const DOC = (path: string) => `${PRODUCT_REPO_URL}/blob/main/${path}`;

export const WORKSPACE_NAV_GROUPS: WorkspaceNavGroup[] = [
  {
    id: "primary",
    labelKey: "navGroupPrimary",
    items: [
      { href: "/", labelKey: "navResearchLibrary", featured: true },
      { href: "/market-watch", labelKey: "navMarketContext" },
      { href: "/post-trade", labelKey: "navPostTradeAnalytics" },
      { href: "/platform", labelKey: "navPlatformOverview" },
    ],
  },
  {
    id: "engine",
    labelKey: "navGroupResearchEngine",
    collapsible: true,
    items: [
      { href: "/engine", labelKey: "navResearchEngineHome" },
      ...ENGINE_STAGES.map((stage) => ({
        href: `/engine/${stage.id}`,
        labelKey: `navEngine_${stage.id}` as TranslationKey,
      })),
    ],
  },
  {
    id: "documentation",
    labelKey: "navGroupDocumentation",
    collapsible: true,
    items: [
      {
        href: DOC("docs/Architecture-Bible/README.md"),
        labelKey: "navDocArchitecture",
        external: true,
      },
      {
        href: DOC("docs/API.md"),
        labelKey: "navDocApi",
        external: true,
      },
      {
        href: DOC("docs/RESEARCH_WORKFLOW.md"),
        labelKey: "navDocMethodology",
        external: true,
      },
      {
        href: DOC("docs/adr/README.md"),
        labelKey: "navDocAdr",
        external: true,
      },
    ],
  },
];

export function isWorkspaceNavItemActive(pathname: string, href: string): boolean {
  if (href.startsWith("http")) {
    return false;
  }
  if (href === "/") {
    return pathname === "/" || pathname.startsWith("/research/");
  }
  if (href === "/platform") {
    return pathname === "/platform";
  }
  if (href === "/engine") {
    // Exact match only — stage/catalog routes activate their own items.
    // Group open-state still covers all /engine* paths via isWorkspaceNavGroupActive.
    return pathname === "/engine";
  }
  if (href.startsWith("/engine/")) {
    return pathname === href || pathname.startsWith(`${href}/`);
  }
  if (href.startsWith("/research/")) {
    return pathname.startsWith("/research/");
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function isWorkspaceNavGroupActive(
  pathname: string,
  group: WorkspaceNavGroup
): boolean {
  if (group.id === "engine" && pathname.startsWith("/engine")) {
    return true;
  }
  if (
    group.id === "primary" &&
    (pathname === "/" ||
      pathname.startsWith("/research/") ||
      pathname === "/platform" ||
      pathname.startsWith("/post-trade") ||
      pathname.startsWith("/market-watch"))
  ) {
    return true;
  }
  return group.items.some((item) => isWorkspaceNavItemActive(pathname, item.href));
}
