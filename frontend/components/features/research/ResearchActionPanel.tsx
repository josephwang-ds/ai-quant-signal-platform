import Button from "@/components/ui/Button";
import type { ResearchWorkspaceSection } from "@/types/research";

export type ResearchActionWorkflowStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error"
  | "awaiting_validation";

export type ResearchActionPanelLabels = {
  title: string;
  description: string;
  addNotebook: string;
  createExperiment: string;
  runValidation: string;
  runningValidation: string;
  requestEvaluation: string;
  openCopilot: string;
  exportResearch: string;
  hintNotebook: string;
  hintExperiment: string;
  hintValidation: string;
  hintEvaluation: string;
  hintEvaluationDisabled: string;
  hintCopilot: string;
  hintCopilotDisabled: string;
  hintExport: string;
};

export type ResearchActionPanelProps = {
  labels: ResearchActionPanelLabels;
  activeSection: ResearchWorkspaceSection;
  onNavigate: (section: ResearchWorkspaceSection) => void;
  onRunValidation: () => void;
  onRequestEvaluation: () => void;
  validationStatus: ResearchActionWorkflowStatus;
  validationRunId: string | null;
  evaluationStatus: ResearchActionWorkflowStatus;
};

type ActionItem = {
  id: string;
  label: string;
  hint: string;
  disabled: boolean;
  onClick?: () => void;
};

/**
 * Right-rail workspace actions.
 * Presentation-only: navigation and workflow callbacks come from ResearchWorkspacePage.
 */
export default function ResearchActionPanel({
  labels,
  activeSection,
  onNavigate,
  onRunValidation,
  onRequestEvaluation,
  validationStatus,
  validationRunId,
  evaluationStatus,
}: ResearchActionPanelProps) {
  const hasValidationEvidence = Boolean(validationRunId);
  const validationLoading = validationStatus === "loading";
  const evaluationLoading = evaluationStatus === "loading";

  const actions: ActionItem[] = [
    {
      id: "notebook",
      label: labels.addNotebook,
      hint: labels.hintNotebook,
      disabled: false,
      onClick: () => onNavigate("notebook"),
    },
    {
      id: "experiments",
      label: labels.createExperiment,
      hint: labels.hintExperiment,
      disabled: false,
      onClick: () => onNavigate("experiments"),
    },
    {
      id: "validation",
      label: validationLoading
        ? labels.runningValidation
        : labels.runValidation,
      hint: labels.hintValidation,
      disabled: validationLoading,
      onClick: onRunValidation,
    },
    {
      id: "evaluation",
      label: labels.requestEvaluation,
      hint: hasValidationEvidence
        ? labels.hintEvaluation
        : labels.hintEvaluationDisabled,
      disabled: !hasValidationEvidence || evaluationLoading,
      onClick: onRequestEvaluation,
    },
    {
      id: "copilot",
      label: labels.openCopilot,
      hint: hasValidationEvidence
        ? labels.hintCopilot
        : labels.hintCopilotDisabled,
      disabled: !hasValidationEvidence,
      onClick: () => onNavigate("copilot"),
    },
    {
      id: "export",
      label: labels.exportResearch,
      hint: labels.hintExport,
      disabled: true,
    },
  ];

  return (
    <aside className="research-action-panel" aria-label={labels.title}>
      <h2 className="research-action-panel__title">{labels.title}</h2>
      <p className="research-action-panel__description">{labels.description}</p>
      <ul className="research-action-panel__list">
        {actions.map((action) => {
          const isActiveTarget =
            (action.id === "notebook" && activeSection === "notebook") ||
            (action.id === "experiments" && activeSection === "experiments") ||
            (action.id === "validation" && activeSection === "validation") ||
            (action.id === "evaluation" && activeSection === "evaluation") ||
            (action.id === "copilot" && activeSection === "copilot");

          return (
            <li key={action.id}>
              <Button
                disabled={action.disabled}
                className={`btn--ghost research-action-panel__button${
                  isActiveTarget ? " is-active" : ""
                }`}
                onClick={action.onClick}
                aria-current={isActiveTarget ? "page" : undefined}
              >
                {action.label}
              </Button>
              <span className="research-action-panel__hint">{action.hint}</span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
