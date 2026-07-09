"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import {
  WORKSPACE_NAV_GROUPS,
  isWorkspaceNavGroupActive,
  isWorkspaceNavItemActive,
} from "@/lib/workspaceNav";

type SideNavProps = {
  language: Language;
};

export default function SideNav({ language }: SideNavProps) {
  const pathname = usePathname();

  return (
    <nav className="workspace-sidenav" aria-label="Workspace modules">
      <Link
        href="/"
        className={`workspace-sidenav__item${pathname === "/" ? " is-active" : ""}`}
      >
        {t(language, "navOverview")}
      </Link>

      {WORKSPACE_NAV_GROUPS.map((group) => (
        <div key={group.id} className="workspace-sidenav__group">
          <p className="workspace-sidenav__group-label">{t(language, group.labelKey)}</p>
          {group.items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`workspace-sidenav__item${
                isWorkspaceNavItemActive(pathname, item.href) ? " is-active" : ""
              }${isWorkspaceNavGroupActive(pathname, group) ? " is-in-group" : ""}`}
            >
              {t(language, item.labelKey)}
            </Link>
          ))}
        </div>
      ))}
    </nav>
  );
}
