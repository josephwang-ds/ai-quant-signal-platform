"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  WORKSPACE_NAV_GROUPS,
  isWorkspaceNavItemActive,
} from "@/lib/workspaceNav";

type SideNavProps = {
  language: Language;
};

export default function SideNav({ language }: SideNavProps) {
  const pathname = usePathname();
  const currentResearchHref = `/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}`;
  const libraryActive = pathname === "/";
  const currentResearchActive = pathname.startsWith("/research/");

  return (
    <nav className="workspace-sidenav" aria-label={t(language, "navAriaPrimary")}>
      <div className="workspace-sidenav__group">
        <span className="workspace-sidenav__group-label" aria-hidden="true">
          {t(language, "navGroupResearch")}
        </span>
        <Link
          href="/"
          className={`workspace-sidenav__item workspace-sidenav__item--primary${
            libraryActive ? " is-active" : ""
          }`}
        >
          {t(language, "navResearchWorkspace")}
        </Link>
        <Link
          href={currentResearchHref}
          className={`workspace-sidenav__item workspace-sidenav__item--primary${
            currentResearchActive ? " is-active" : ""
          }`}
        >
          {t(language, "navCurrentResearch")}
        </Link>
      </div>

      <details className="workspace-sidenav__group workspace-sidenav__group--secondary">
        <summary className="workspace-sidenav__group-label workspace-sidenav__summary">
          {t(language, "navGroupSecondary")}
        </summary>
        {WORKSPACE_NAV_GROUPS.map((group) => (
          <div key={group.id} className="workspace-sidenav__subgroup">
            <span className="workspace-sidenav__subgroup-label" aria-hidden="true">
              {t(language, group.labelKey)}
            </span>
            {group.items.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`workspace-sidenav__item${
                  isWorkspaceNavItemActive(pathname, item.href) ? " is-active" : ""
                }`}
              >
                {t(language, item.labelKey)}
              </Link>
            ))}
          </div>
        ))}
      </details>
    </nav>
  );
}
