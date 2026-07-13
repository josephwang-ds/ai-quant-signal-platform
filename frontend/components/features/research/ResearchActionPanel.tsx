import Button from "@/components/ui/Button";

export type ResearchActionPanelLabels = {
  title: string;
  description: string;
  addNotebook: string;
  createExperiment: string;
  runValidation: string;
  requestEvaluation: string;
  exportResearch: string;
  comingLater: string;
};

export type ResearchActionPanelProps = {
  labels: ResearchActionPanelLabels;
};

const ACTIONS = [
  "addNotebook",
  "createExperiment",
  "runValidation",
  "requestEvaluation",
  "exportResearch",
] as const;

/**
 * 右侧行动面板：动作可点击但全部为后续 PR 占位（disabled）。
 * 不实现任何工作流。
 */
export default function ResearchActionPanel({ labels }: ResearchActionPanelProps) {
  const actionLabel: Record<(typeof ACTIONS)[number], string> = {
    addNotebook: labels.addNotebook,
    createExperiment: labels.createExperiment,
    runValidation: labels.runValidation,
    requestEvaluation: labels.requestEvaluation,
    exportResearch: labels.exportResearch,
  };

  return (
    <aside className="research-action-panel" aria-label={labels.title}>
      <h2 className="research-action-panel__title">{labels.title}</h2>
      <p className="research-action-panel__description">{labels.description}</p>
      <ul className="research-action-panel__list">
        {ACTIONS.map((action) => (
          <li key={action}>
            <Button disabled className="btn--ghost research-action-panel__button">
              {actionLabel[action]}
            </Button>
            <span className="research-action-panel__hint">{labels.comingLater}</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
