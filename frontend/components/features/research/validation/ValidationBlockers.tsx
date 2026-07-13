import StatusBadge from "@/components/ui/StatusBadge";
import type { ValidationBlocker } from "@/types/validation";

export type ValidationBlockersLabels = {
  title: string;
  description: string;
  severity: string;
  reason: string;
  stage: string;
  nextAction: string;
  empty: string;
  inspect: string;
};

type ValidationBlockersProps = {
  blockers: ValidationBlocker[];
  labels: ValidationBlockersLabels;
  onInspectStage?: (stageId: string) => void;
};

function severityVariant(
  severity: ValidationBlocker["severity"]
): "danger" | "warning" | "info" {
  switch (severity) {
    case "blocking":
      return "danger";
    case "warning":
      return "warning";
    default:
      return "info";
  }
}

export default function ValidationBlockers({
  blockers,
  labels,
  onInspectStage,
}: ValidationBlockersProps) {
  return (
    <section className="validation-blockers" aria-label={labels.title}>
      <header className="validation-blockers__header">
        <h3 className="validation-blockers__title">{labels.title}</h3>
        <p className="section-meta">{labels.description}</p>
      </header>

      {blockers.length === 0 ? (
        <p className="validation-blockers__empty">{labels.empty}</p>
      ) : (
        <ul className="validation-blockers__list">
          {blockers.map((blocker) => (
            <li key={blocker.id} className="validation-blockers__item">
              <div className="validation-blockers__item-head">
                <StatusBadge
                  label={blocker.severity}
                  variant={severityVariant(blocker.severity)}
                />
                <strong>{blocker.affectedStageName}</strong>
              </div>
              <dl className="validation-blockers__dl">
                <div>
                  <dt>{labels.reason}</dt>
                  <dd>{blocker.reason}</dd>
                </div>
                <div>
                  <dt>{labels.stage}</dt>
                  <dd>{blocker.affectedStageName}</dd>
                </div>
                <div>
                  <dt>{labels.nextAction}</dt>
                  <dd>{blocker.requiredNextAction}</dd>
                </div>
              </dl>
              {onInspectStage ? (
                <button
                  type="button"
                  className="btn btn--ghost"
                  onClick={() => onInspectStage(blocker.affectedStageId)}
                >
                  {labels.inspect}
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
