"use client";

import type { WorkflowStepId, WorkflowStepState } from "@/lib/researchWorkflow";

export type GuidedResearchFlowLabels = {
  title: string;
  stepRunResearch: string;
  stepValidateEvidence: string;
  stepReviewEvaluation: string;
  stepAskCopilot: string;
  unavailableAfterExecution: string;
  unavailableAfterValidation: string;
  unavailableAfterEvaluation: string;
  loading: string;
  failed: string;
};

export type GuidedResearchFlowProps = {
  stepStates: Record<WorkflowStepId, WorkflowStepState>;
  primaryStep: WorkflowStepId;
  labels: GuidedResearchFlowLabels;
};

const STEP_ORDER: WorkflowStepId[] = [
  "research",
  "validation",
  "evaluation",
  "copilot",
];

function stepLabel(step: WorkflowStepId, labels: GuidedResearchFlowLabels): string {
  if (step === "research") return labels.stepRunResearch;
  if (step === "validation") return labels.stepValidateEvidence;
  if (step === "evaluation") return labels.stepReviewEvaluation;
  return labels.stepAskCopilot;
}

function stepHint(
  step: WorkflowStepId,
  state: WorkflowStepState,
  labels: GuidedResearchFlowLabels
): string | null {
  if (state === "loading") return labels.loading;
  if (state === "failed") return labels.failed;
  if (state !== "unavailable") return null;
  if (step === "validation") return labels.unavailableAfterExecution;
  if (step === "evaluation") return labels.unavailableAfterValidation;
  if (step === "copilot") return labels.unavailableAfterEvaluation;
  return null;
}

function statusGlyph(state: WorkflowStepState): string {
  if (state === "completed") return "✓";
  if (state === "loading") return "…";
  if (state === "failed") return "!";
  return "•";
}

export default function GuidedResearchFlow({
  stepStates,
  primaryStep,
  labels,
}: GuidedResearchFlowProps) {
  return (
    <section className="guided-research-flow" aria-label={labels.title}>
      <h3 className="overview-block__title">{labels.title}</h3>
      <ol className="research-guided-steps">
        {STEP_ORDER.map((step) => {
          const state = stepStates[step];
          const hint = stepHint(step, state, labels);
          return (
            <li
              key={step}
              className={`research-guided-step research-guided-step--${state}${
                primaryStep === step ? " is-current" : ""
              }`}
            >
              <span className="research-guided-step__name">{stepLabel(step, labels)}</span>
              <span className="research-guided-step__status" aria-hidden="true">
                {statusGlyph(state)}
              </span>
              {hint ? (
                <span className="research-guided-step__hint section-meta">{hint}</span>
              ) : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
