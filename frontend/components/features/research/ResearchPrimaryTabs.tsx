"use client";

import Link from "next/link";
import {
  RESEARCH_WORKSPACE_PRIMARY_SECTIONS,
  type ResearchWorkspacePrimarySection,
  type ResearchWorkspaceSection,
} from "@/types/research";
import {
  derivePrimaryTabProgress,
  sectionToWorkflowStep,
  type PrimaryTabProgress,
  type WorkflowStepId,
  type WorkflowStepState,
} from "@/lib/researchWorkflow";

export type ResearchPrimaryTabsLabels = Record<
  ResearchWorkspacePrimarySection,
  string
> & {
  progressCompleted: string;
  progressCurrent: string;
  progressLocked: string;
};

export type ResearchPrimaryTabsProps = {
  researchId: string;
  activeSection: ResearchWorkspaceSection;
  stepStates: Record<WorkflowStepId, WorkflowStepState>;
  labels: ResearchPrimaryTabsLabels;
};

function sectionHref(researchId: string, section: ResearchWorkspaceSection): string {
  return section === "overview"
    ? `/research/${encodeURIComponent(researchId)}`
    : `/research/${encodeURIComponent(researchId)}?tab=${section}`;
}

function isSectionActive(
  section: ResearchWorkspaceSection,
  activeSection: ResearchWorkspaceSection
): boolean {
  return (
    section === activeSection ||
    (section === "validation" && activeSection === "evaluation")
  );
}

function progressStatusLabel(
  progress: PrimaryTabProgress,
  labels: ResearchPrimaryTabsLabels
): string {
  if (progress === "completed") return labels.progressCompleted;
  if (progress === "current") return labels.progressCurrent;
  if (progress === "locked") return labels.progressLocked;
  return "";
}

function ProgressGlyph({ progress }: { progress: PrimaryTabProgress }) {
  if (progress === "completed") {
    return (
      <span className="research-workspace__primary-tab-glyph" aria-hidden="true">
        ✓
      </span>
    );
  }
  if (progress === "locked") {
    return (
      <span className="research-workspace__primary-tab-glyph" aria-hidden="true">
        <svg
          className="research-workspace__primary-tab-lock"
          viewBox="0 0 16 16"
          width="11"
          height="11"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            x="3.5"
            y="7"
            width="9"
            height="7"
            rx="1.2"
            stroke="currentColor"
            strokeWidth="1.4"
          />
          <path
            d="M5.5 7V5.2a2.5 2.5 0 0 1 5 0V7"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
          />
        </svg>
      </span>
    );
  }
  return null;
}

/**
 * Primary lifecycle tabs — also the sole stage progress indicator.
 * Secondary tools stay in the separate "More" menu on the workspace page.
 */
export default function ResearchPrimaryTabs({
  researchId,
  activeSection,
  stepStates,
  labels,
}: ResearchPrimaryTabsProps) {
  return (
    <div
      className="research-workspace__primary-tabs"
      role="group"
      aria-label="Research lifecycle"
    >
      {RESEARCH_WORKSPACE_PRIMARY_SECTIONS.map((section) => {
        const step = sectionToWorkflowStep(section);
        const state = stepStates[step];
        const progress = derivePrimaryTabProgress(state);
        const active = isSectionActive(section, activeSection);
        const statusLabel = progressStatusLabel(progress, labels);
        const name = labels[section];

        return (
          <Link
            key={section}
            href={sectionHref(researchId, section)}
            className={[
              "research-workspace__primary-tab",
              `research-workspace__primary-tab--${progress}`,
              active ? "is-active" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            aria-current={active ? "page" : undefined}
            aria-label={statusLabel ? `${name}, ${statusLabel}` : name}
            data-progress={progress}
            title={statusLabel || undefined}
          >
            <ProgressGlyph progress={progress} />
            <span className="research-workspace__primary-tab-label">{name}</span>
          </Link>
        );
      })}
    </div>
  );
}
