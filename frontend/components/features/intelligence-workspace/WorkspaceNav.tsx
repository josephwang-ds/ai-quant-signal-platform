"use client";

import Link from "next/link";
import type { Language } from "@/lib/i18n";
import {
  WORKSPACE_VIEWS,
  workspaceViewHref,
  type WorkspaceView,
} from "@/lib/intelligence/workspaceDisplay";

export type WorkspaceNavProps = {
  runId: string;
  activeView: WorkspaceView;
  language: Language;
};

const VIEW_LABELS: Record<WorkspaceView, { en: string; zh: string }> = {
  overview: { en: "Overview", zh: "概览" },
  signals: { en: "Signals", zh: "信号" },
  evidence: { en: "Evidence", zh: "证据" },
  validation: { en: "Validation", zh: "验证" },
};

export default function WorkspaceNav({
  runId,
  activeView,
  language,
}: WorkspaceNavProps) {
  const zh = language === "zh";

  return (
    <nav
      className="published-workspace__nav"
      aria-label={zh ? "已发布工作区视图" : "Published workspace views"}
      data-testid="published-workspace-nav"
    >
      <ul className="published-workspace__nav-list">
        {WORKSPACE_VIEWS.map((view) => {
          const active = view === activeView;
          return (
            <li key={view}>
              <Link
                href={workspaceViewHref(runId, view)}
                scroll={false}
                className={`published-workspace__nav-link${active ? " is-active" : ""}`}
                aria-current={active ? "page" : undefined}
                data-testid={`workspace-nav-${view}`}
              >
                {VIEW_LABELS[view][language]}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
