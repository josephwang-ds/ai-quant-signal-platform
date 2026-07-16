"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import {
  WORKSPACE_NAV_GROUPS,
  isWorkspaceNavItemActive,
} from "@/lib/workspaceNav";

type SideNavProps = {
  language: Language;
};

export default function SideNav({ language }: SideNavProps) {
  const pathname = usePathname();

  return (
    <nav className="workspace-sidenav" aria-label="Workspace modules">
      <div className="workspace-sidenav__group">
        <span className="workspace-sidenav__group-label" aria-hidden="true">
          {t(language, "navGroupResearch")}
        </span>
        <Link
          href="/"
          className={`workspace-sidenav__item${
            pathname === "/" || pathname.startsWith("/research/")
              ? " is-active"
              : ""
          }`}
        >
          {t(language, "navResearchWorkspace")}
        </Link>
        <Link
          href="/overview"
          className={`workspace-sidenav__item${
            pathname === "/overview" ? " is-active" : ""
          }`}
        >
          {t(language, "navOverview")}
        </Link>
      </div>

      {WORKSPACE_NAV_GROUPS.map((group) => (
        <div key={group.id} className="workspace-sidenav__group">
          <span className="workspace-sidenav__group-label" aria-hidden="true">
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
    </nav>
  );
}
