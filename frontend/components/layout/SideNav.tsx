"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
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
  const className = `workspace-sidenav__item${
    item.featured ? " workspace-sidenav__item--featured" : ""
  }${active ? " is-active" : ""}`;
  const label = (
    <>
      <span className="workspace-sidenav__item-label">{t(language, item.labelKey)}</span>
      {item.featured ? (
        <span className="workspace-sidenav__featured-mark" aria-hidden="true">
          ★
        </span>
      ) : null}
    </>
  );

  if (item.external) {
    return (
      <a
        href={item.href}
        className={className}
        target="_blank"
        rel="noopener noreferrer"
        onClick={onNavigate}
      >
        {label}
      </a>
    );
  }

  return (
    <Link
      href={item.href}
      className={className}
      aria-current={active ? "page" : undefined}
      onClick={onNavigate}
    >
      {label}
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
  const groupActive = group.collapsible
    ? isWorkspaceNavGroupActive(pathname, group)
    : false;
  const storageKey = `workspace-sidenav-open:${group.id}`;

  // Persisted, sticky open state: auto-opens when the active route enters
  // this group, but never auto-closes on navigation — only an explicit user
  // toggle closes it. Uncontrolled `open={groupActive}` used to force-close
  // this on every route change, hiding primary nav on every navigation.
  //
  // Initial state must be identical on server and client (just `groupActive`)
  // to avoid a hydration mismatch; the stored preference is only applied in
  // an effect after mount, which runs client-side only.
  const [open, setOpen] = useState<boolean>(groupActive);

  useEffect(() => {
    const stored = window.localStorage.getItem(storageKey);
    if (stored === "true") setOpen(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (groupActive) setOpen(true);
  }, [groupActive]);

  if (group.collapsible) {
    return (
      <details
        className="workspace-sidenav__group workspace-sidenav__group--collapsible"
        open={open}
        onToggle={(event) => {
          const next = event.currentTarget.open;
          setOpen(next);
          window.localStorage.setItem(storageKey, String(next));
        }}
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
