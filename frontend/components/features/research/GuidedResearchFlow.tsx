"use client";

import {
  WORKFLOW_STEP_ORDER,
  type WorkflowStepId,
  type WorkflowStepState,
} from "@/lib/researchWorkflow";

export type GuidedResearchFlowLabels = {
  title: string;
  stepResearch: string;
  stepExperiment: string;
  stepValidation: string;
  stepRobustness: string;
  stepPaper: string;
  stepDecision: string;
  stepArchive: string;
  unavailableUntilPrior: string;
  loading: string;
  failed: string;
};

export type GuidedResearchFlowProps = {
  stepStates: Record<WorkflowStepId, WorkflowStepState>;
  primaryStep: WorkflowStepId;
  labels: GuidedResearchFlowLabels;
};

function stepLabel(step: WorkflowStepId, labels: GuidedResearchFlowLabels): string {
  if (step === "research") return labels.stepResearch;
  if (step === "experiment") return labels.stepExperiment;
  if (step === "validation") return labels.stepValidation;
  if (step === "robustness") return labels.stepRobustness;
  if (step === "paper") return labels.stepPaper;
  if (step === "decision") return labels.stepDecision;
  return labels.stepArchive;
}

function stepHint(
  state: WorkflowStepState,
  labels: GuidedResearchFlowLabels
): string | null {
  if (state === "loading") return labels.loading;
  if (state === "failed") return labels.failed;
  if (state === "unavailable") return labels.unavailableUntilPrior;
  return null;
}

export default function GuidedResearchFlow({
  stepStates,
  primaryStep,
  labels,
}: GuidedResearchFlowProps) {
  return (
    <section className="guided-research-flow" aria-label={labels.title || undefined}>
      {labels.title ? <h3 className="overview-block__title">{labels.title}</h3> : null}
      <ol className="workflow-stepper">
        {WORKFLOW_STEP_ORDER.map((step, index) => {
          const state = stepStates[step];
          const isCurrent = primaryStep === step;
          const hint = stepHint(state, labels);
          const isLast = index === WORKFLOW_STEP_ORDER.length - 1;

          return (
            <li
              key={step}
              className={`workflow-stepper__step workflow-stepper__step--${state}${
                isCurrent ? " is-current" : ""
              }`}
            >
              <div className="workflow-stepper__marker-wrap">
                <span className="workflow-stepper__marker" aria-hidden="true">
                  {state === "completed" ? "✓" : index + 1}
                </span>
                {!isLast ? (
                  <span
                    className={`workflow-stepper__connector${
                      state === "completed" ? " workflow-stepper__connector--done" : ""
                    }`}
                    aria-hidden="true"
                  />
                ) : null}
              </div>
              <div className="workflow-stepper__content">
                <span className="workflow-stepper__name">{stepLabel(step, labels)}</span>
                {hint ? (
                  <span className="workflow-stepper__hint section-meta">{hint}</span>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
