import {
  RESEARCH_PROGRESS_STAGES,
  type ResearchProgressStage,
} from "@/types/research";
import { getLifecycleStepState } from "@/lib/researchWorkspace";

export type LifecycleProgressProps = {
  currentStage: ResearchProgressStage;
  title?: string;
  description?: string;
};

/**
 * Research 生命周期进度（可复用）。
 * 阶段序列对齐 Architecture Bible Ch3。
 */
export default function LifecycleProgress({
  currentStage,
  title = "Research lifecycle",
  description,
}: LifecycleProgressProps) {
  return (
    <section className="lifecycle-progress" aria-label={title}>
      <header className="lifecycle-progress__header">
        <h3 className="lifecycle-progress__title">{title}</h3>
        {description ? (
          <p className="lifecycle-progress__description">{description}</p>
        ) : null}
      </header>
      <ol className="lifecycle-progress__track">
        {RESEARCH_PROGRESS_STAGES.map((stage) => {
          const state = getLifecycleStepState(stage, currentStage);
          return (
            <li
              key={stage}
              className={`lifecycle-progress__step lifecycle-progress__step--${state}`}
            >
              <span className="lifecycle-progress__marker" aria-hidden="true" />
              <span className="lifecycle-progress__label">{stage}</span>
              <span className="lifecycle-progress__state">
                {state === "completed"
                  ? "Completed"
                  : state === "current"
                    ? "Current"
                    : "Upcoming"}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
