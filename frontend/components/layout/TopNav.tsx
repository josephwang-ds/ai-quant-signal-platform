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

type TopNavProps = {
  language: Language;
};

export default function TopNav({ language }: TopNavProps) {
  const pathname = usePathname();

  return (
    <nav className="dashboard-nav" aria-label="Workspace modules">
      <Link href="/" className={pathname === "/" ? "is-active" : undefined}>
        {t(language, "navResearchWorkspace")}
      </Link>
      <Link
        href="/overview"
        className={pathname === "/overview" ? "is-active" : undefined}
      >
        {t(language, "navOverview")}
      </Link>

      {WORKSPACE_NAV_GROUPS.map((group) => {
        const groupActive = isWorkspaceNavGroupActive(pathname, group);
        return (
          <details
            key={group.id}
            className={`dashboard-nav-group${groupActive ? " is-group-active" : ""}`}
            open={groupActive || undefined}
          >
            <summary>{t(language, group.labelKey)}</summary>
            <div className="dashboard-nav-group__menu" role="menu">
              {group.items.map((item) => (
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
              ))}
            </div>
          </details>
        );
      })}
    </nav>
  );
}
