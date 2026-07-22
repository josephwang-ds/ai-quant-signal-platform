import Link from "next/link";
import {
  RESEARCH_WORKSPACE_PRIMARY_SECTIONS,
  RESEARCH_WORKSPACE_TOOL_SECTIONS,
  type ResearchWorkspaceSection,
} from "@/types/research";
import {
  derivePrimaryTabProgress,
  sectionToWorkflowStep,
  type WorkflowStepId,
  type WorkflowStepState,
} from "@/lib/researchWorkflow";

export type ResearchWorkspaceNavigationLabels = Record<
  ResearchWorkspaceSection,
  string
>;

export type ResearchWorkspaceNavigationProps = {
  researchId: string;
  activeSection: ResearchWorkspaceSection;
  labels: ResearchWorkspaceNavigationLabels;
  toolsLabel?: string;
  /** When provided, primary tabs also show lifecycle progress (completed / current / locked). */
  stepStates?: Record<WorkflowStepId, WorkflowStepState>;
};

function sectionHref(researchId: string, section: ResearchWorkspaceSection): string {
  return section === "overview"
    ? `/research/${encodeURIComponent(researchId)}`
    : `/research/${encodeURIComponent(researchId)}?tab=${section}`;
}

function isPrimaryActive(
  section: ResearchWorkspaceSection,
  activeSection: ResearchWorkspaceSection
): boolean {
  return (
    section === activeSection ||
    (section === "validation" && activeSection === "evaluation")
  );
}

/** Research-local left navigation — lifecycle spine first; tools remain URL-compatible. */
export default function ResearchWorkspaceNavigation({
  researchId,
  activeSection,
  labels,
  toolsLabel = "Tools",
  stepStates,
}: ResearchWorkspaceNavigationProps) {
  return (
    <nav
      className="research-workspace-nav research-workspace-nav--sidebar"
      aria-label="Research workspace sections"
    >
      <ul className="research-workspace-nav__list">
        {RESEARCH_WORKSPACE_PRIMARY_SECTIONS.map((section) => {
          const href = sectionHref(researchId, section);
          const isActive = isPrimaryActive(section, activeSection);
          const progress = stepStates
            ? derivePrimaryTabProgress(stepStates[sectionToWorkflowStep(section)])
            : null;
          return (
            <li key={section}>
              <Link
                href={href}
                className={[
                  "research-workspace-nav__item",
                  isActive ? "is-active" : "",
                  progress ? `research-workspace-nav__item--${progress}` : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                aria-current={isActive ? "page" : undefined}
                data-progress={progress ?? undefined}
              >
                {progress === "completed" ? (
                  <span aria-hidden="true">✓ </span>
                ) : null}
                {progress === "locked" ? (
                  <span aria-hidden="true">⊘ </span>
                ) : null}
                {labels[section]}
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="research-workspace-nav__tools">
        <p className="research-workspace-nav__tools-label">{toolsLabel}</p>
        <ul className="research-workspace-nav__list research-workspace-nav__list--tools">
          {RESEARCH_WORKSPACE_TOOL_SECTIONS.map((section) => {
            const href = sectionHref(researchId, section);
            const isActive = section === activeSection;
            return (
              <li key={section}>
                <Link
                  href={href}
                  className={`research-workspace-nav__item${
                    isActive ? " is-active" : ""
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  {labels[section]}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
