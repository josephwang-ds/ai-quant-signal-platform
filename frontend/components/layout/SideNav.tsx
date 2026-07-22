"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import {
  WORKSPACE_NAV_GROUPS,
  isWorkspaceNavGroupActive,
  isWorkspaceNavItemActive,
  type WorkspaceNavGroup,
  type WorkspaceNavItem,
} from "@/lib/workspaceNav";

type SideNavProps = {
  language: Language;
  onNavigate?: () => void;
};

function NavLink({
  language,
  item,
  onNavigate,
}: {
  language: Language;
  item: WorkspaceNavItem;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const active = isWorkspaceNavItemActive(pathname, item.href);

  return (
    <Link
      href={item.href}
      className={`workspace-sidenav__item${
        item.featured ? " workspace-sidenav__item--featured" : ""
      }${active ? " is-active" : ""}`}
      aria-current={active ? "page" : undefined}
      onClick={onNavigate}
    >
      <span className="workspace-sidenav__item-label">{t(language, item.labelKey)}</span>
      {item.featured ? (
        <span className="workspace-sidenav__featured-mark" aria-hidden="true">
          ★
        </span>
      ) : null}
    </Link>
  );
}

function NavGroupSection({
  language,
  group,
  onNavigate,
}: {
  language: Language;
  group: WorkspaceNavGroup;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  if (group.collapsible) {
    const groupActive = isWorkspaceNavGroupActive(pathname, group);
    return (
      <details
        className="workspace-sidenav__group workspace-sidenav__group--archive"
        open={groupActive || undefined}
      >
        <summary className="workspace-sidenav__group-label workspace-sidenav__summary">
          {t(language, group.labelKey)}
        </summary>
        {group.items.map((item) => (
          <NavLink
            key={item.href}
            language={language}
            item={item}
            onNavigate={onNavigate}
          />
        ))}
      </details>
    );
  }

  return (
    <div className="workspace-sidenav__group">
      <span className="workspace-sidenav__group-label">
        {t(language, group.labelKey)}
      </span>
      {group.items.map((item) => (
        <NavLink
          key={item.href}
          language={language}
          item={item}
          onNavigate={onNavigate}
        />
      ))}
    </div>
  );
}

export default function SideNav({ language, onNavigate }: SideNavProps) {
  return (
    <nav className="workspace-sidenav" aria-label={t(language, "navAriaPrimary")}>
      {WORKSPACE_NAV_GROUPS.map((group) => (
        <NavGroupSection
          key={group.id}
          language={language}
          group={group}
          onNavigate={onNavigate}
        />
      ))}
    </nav>
  );
}
