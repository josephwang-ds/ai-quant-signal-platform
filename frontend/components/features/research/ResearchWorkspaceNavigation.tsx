import Link from "next/link";
import {
  RESEARCH_WORKSPACE_SECTIONS,
  type ResearchWorkspaceSection,
} from "@/types/research";

export type ResearchWorkspaceNavigationLabels = Record<
  ResearchWorkspaceSection,
  string
>;

export type ResearchWorkspaceNavigationProps = {
  researchId: string;
  activeSection: ResearchWorkspaceSection;
  labels: ResearchWorkspaceNavigationLabels;
};

/** 研究工作区内局部导航（tabs）。 */
export default function ResearchWorkspaceNavigation({
  researchId,
  activeSection,
  labels,
}: ResearchWorkspaceNavigationProps) {
  return (
    <nav className="research-workspace-nav" aria-label="Research workspace sections">
      <ul className="research-workspace-nav__list">
        {RESEARCH_WORKSPACE_SECTIONS.map((section) => {
          const href =
            section === "overview"
              ? `/research/${encodeURIComponent(researchId)}`
              : `/research/${encodeURIComponent(researchId)}?section=${section}`;
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
    </nav>
  );
}
