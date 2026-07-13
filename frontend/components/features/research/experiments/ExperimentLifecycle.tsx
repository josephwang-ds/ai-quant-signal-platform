import {
  EXPERIMENT_PROGRESS_STAGES,
  type ExperimentStatus,
} from "@/types/experiment";
import { getExperimentLifecycleStepState } from "@/lib/researchExperiments";

export type ExperimentLifecycleLabels = {
  title: string;
  description: string;
  completed: string;
  current: string;
  upcoming: string;
  terminalNote: string;
  governedNote: string;
};

type ExperimentLifecycleProps = {
  status: ExperimentStatus;
  labels: ExperimentLifecycleLabels;
};

/**
 * Experiment 生命周期（对齐 Ch3）。
 * UI 不提供静默状态跃迁；治理动作延后。
 */
export default function ExperimentLifecycle({
  status,
  labels,
}: ExperimentLifecycleProps) {
  const isTerminal = status === "Failed" || status === "Invalidated";

  return (
    <section className="experiment-lifecycle" aria-label={labels.title}>
      <header className="experiment-lifecycle__header">
        <h4 className="experiment-lifecycle__title">{labels.title}</h4>
        <p className="experiment-lifecycle__description">{labels.description}</p>
      </header>

      <ol className="experiment-lifecycle__track">
        {EXPERIMENT_PROGRESS_STAGES.map((stage) => {
          const state = getExperimentLifecycleStepState(stage, status);
          return (
            <li
              key={stage}
              className={`experiment-lifecycle__step experiment-lifecycle__step--${state}`}
            >
              <span className="experiment-lifecycle__marker" aria-hidden="true" />
              <span className="experiment-lifecycle__label">{stage}</span>
              <span className="experiment-lifecycle__state">
                {state === "completed"
                  ? labels.completed
                  : state === "current"
                    ? labels.current
                    : labels.upcoming}
              </span>
            </li>
          );
        })}
      </ol>

      {isTerminal ? (
        <p className="experiment-lifecycle__terminal">
          {labels.terminalNote}: <strong>{status}</strong>
        </p>
      ) : null}

      <p className="section-meta">{labels.governedNote}</p>
    </section>
  );
}
