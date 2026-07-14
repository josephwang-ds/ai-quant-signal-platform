import type { PlannedValidationStage } from "@/types/canonicalResearch";

export type ValidationStageDisplayStatus =
  | "not_started"
  | "awaiting_data"
  | "completed";

export type ValidationPendingPanelLabels = {
  title: string;
  summary: string;
  notStarted: string;
  awaitingData: string;
  completed: string;
  note: string;
};

type ValidationPendingPanelProps = {
  stages: PlannedValidationStage[];
  statusForStage: (stageId: string) => ValidationStageDisplayStatus;
  labels: ValidationPendingPanelLabels;
};

function statusLabel(
  status: ValidationStageDisplayStatus,
  labels: ValidationPendingPanelLabels
): string {
  if (status === "completed") {
    return labels.completed;
  }
  if (status === "awaiting_data") {
    return labels.awaitingData;
  }
  return labels.notStarted;
}

/**
 * Validation stages — only engine-supported outcomes may be Completed.
 */
export default function ValidationPendingPanel({
  stages,
  statusForStage,
  labels,
}: ValidationPendingPanelProps) {
  return (
    <section className="validation-pending-panel" aria-label={labels.title}>
      <h2 className="validation-pending-panel__title">{labels.title}</h2>
      <p className="validation-pending-panel__summary">{labels.summary}</p>
      <ul className="validation-pending-panel__list">
        {stages.map((stage) => {
          const status = statusForStage(stage.id);
          return (
            <li key={stage.id} className="validation-pending-panel__item">
              <div className="validation-pending-panel__item-head">
                <h3>{stage.name}</h3>
                <span
                  className={`badge badge--${
                    status === "completed" ? "success" : "neutral"
                  }`}
                >
                  {statusLabel(status, labels)}
                </span>
              </div>
              <p>{stage.description}</p>
            </li>
          );
        })}
      </ul>
      <p className="validation-pending-panel__note">{labels.note}</p>
    </section>
  );
}
