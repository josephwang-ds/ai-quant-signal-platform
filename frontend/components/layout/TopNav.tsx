"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  WORKSPACE_NAV_GROUPS,
  isWorkspaceNavGroupActive,
  isWorkspaceNavItemActive,
} from "@/lib/workspaceNav";

type TopNavProps = {
  language: Language;
};

export default function TopNav({ language }: TopNavProps) {
  const pathname = usePathname();
  const currentResearchHref = `/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}`;
  const secondaryActive = WORKSPACE_NAV_GROUPS.some((group) =>
    isWorkspaceNavGroupActive(pathname, group)
  );

  return (
    <nav className="dashboard-nav" aria-label={t(language, "navAriaPrimary")}>
      <Link
        href="/"
        className={pathname === "/" ? "is-active" : undefined}
      >
        {t(language, "navResearchWorkspace")}
      </Link>
      <Link
        href={currentResearchHref}
        className={pathname.startsWith("/research/") ? "is-active" : undefined}
      >
        {t(language, "navCurrentResearch")}
      </Link>

      <details
        className={`dashboard-nav-group dashboard-nav-group--secondary${
          secondaryActive ? " is-group-active" : ""
        }`}
        open={secondaryActive || undefined}
      >
        <summary>{t(language, "navGroupSecondary")}</summary>
        <div className="dashboard-nav-group__menu" role="menu">
          {WORKSPACE_NAV_GROUPS.flatMap((group) =>
            group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                role="menuitem"
                className={
                  isWorkspaceNavItemActive(pathname, item.href) ? "is-active" : undefined
                }
              >
                {t(language, item.labelKey)}
              </Link>
            ))
          )}
        </div>
      </details>
    </nav>
  );
}
