"use client";

import Button from "@/components/ui/Button";
import type { WorkflowStepId } from "@/lib/researchWorkflow";

export type NextStepPanelLabels = {
  title: string;
  runResearchTitle: string;
  runResearchDescription: string;
  runResearchCta: string;
  runResearchLoadingCta: string;
  runResearchRetryCta: string;
  validateTitle: string;
  validateDescription: string;
  validateCta: string;
  evaluateTitle: string;
  evaluateDescription: string;
  evaluateCta: string;
  copilotTitle: string;
  copilotDescription: string;
  copilotCta: string;
};

export type NextStepPanelProps = {
  step: WorkflowStepId;
  disabled: boolean;
  executionFailed: boolean;
  labels: NextStepPanelLabels;
  onRunResearch: () => void;
  onRunValidation: () => void;
  onRequestEvaluation: () => void;
  onAskCopilot: () => void;
};

export default function NextStepPanel({
  step,
  disabled,
  executionFailed,
  labels,
  onRunResearch,
  onRunValidation,
  onRequestEvaluation,
  onAskCopilot,
}: NextStepPanelProps) {
  const content = (() => {
    if (step === "research") {
      return {
        title: labels.runResearchTitle,
        description: labels.runResearchDescription,
        cta: executionFailed
          ? labels.runResearchRetryCta
          : disabled
            ? labels.runResearchLoadingCta
            : labels.runResearchCta,
        onClick: onRunResearch,
      };
    }
    if (step === "validation") {
      return {
        title: labels.validateTitle,
        description: labels.validateDescription,
        cta: labels.validateCta,
        onClick: onRunValidation,
      };
    }
    if (step === "evaluation") {
      return {
        title: labels.evaluateTitle,
        description: labels.evaluateDescription,
        cta: labels.evaluateCta,
        onClick: onRequestEvaluation,
      };
    }
    return {
      title: labels.copilotTitle,
      description: labels.copilotDescription,
      cta: labels.copilotCta,
      onClick: onAskCopilot,
    };
  })();

  return (
    <aside className="next-step-panel" aria-label={labels.title}>
      <p className="next-step-panel__eyebrow">{labels.title}</p>
      <h3 className="next-step-panel__title">{content.title}</h3>
      <p className="next-step-panel__description section-meta">{content.description}</p>
      <Button primary disabled={disabled} onClick={content.onClick}>
        {content.cta}
      </Button>
    </aside>
  );
}
