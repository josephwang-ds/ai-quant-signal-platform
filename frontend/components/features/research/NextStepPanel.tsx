"use client";

import ResearchNextAction from "@/components/features/research/ux/ResearchNextAction";
import type { WorkflowStepId } from "@/lib/researchWorkflow";
import { workflowStepToSection } from "@/lib/researchWorkflow";
import type { ResearchWorkspaceSection } from "@/types/research";

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
  openExperimentTitle: string;
  openExperimentDescription: string;
  openExperimentCta: string;
  openRobustnessTitle: string;
  openRobustnessDescription: string;
  openRobustnessCta: string;
  openPaperTitle: string;
  openPaperDescription: string;
  openPaperCta: string;
  openDecisionTitle: string;
  openDecisionDescription: string;
  openDecisionCta: string;
  openArchiveTitle: string;
  openArchiveDescription: string;
  openArchiveCta: string;
};

export type NextStepPanelProps = {
  step: WorkflowStepId;
  disabled: boolean;
  executionFailed: boolean;
  labels: NextStepPanelLabels;
  onRunResearch: () => void;
  onRunValidation: () => void;
  onOpenSection: (section: ResearchWorkspaceSection) => void;
};

export default function NextStepPanel({
  step,
  disabled,
  executionFailed,
  labels,
  onRunResearch,
  onRunValidation,
  onOpenSection,
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
    if (step === "experiment") {
      return {
        title: labels.openExperimentTitle,
        description: labels.openExperimentDescription,
        cta: labels.openExperimentCta,
        onClick: () => onOpenSection(workflowStepToSection("experiment")),
      };
    }
    if (step === "robustness") {
      return {
        title: labels.openRobustnessTitle,
        description: labels.openRobustnessDescription,
        cta: labels.openRobustnessCta,
        onClick: () => onOpenSection(workflowStepToSection("robustness")),
      };
    }
    if (step === "paper") {
      return {
        title: labels.openPaperTitle,
        description: labels.openPaperDescription,
        cta: labels.openPaperCta,
        onClick: () => onOpenSection(workflowStepToSection("paper")),
      };
    }
    if (step === "decision") {
      return {
        title: labels.openDecisionTitle,
        description: labels.openDecisionDescription,
        cta: labels.openDecisionCta,
        onClick: () => onOpenSection(workflowStepToSection("decision")),
      };
    }
    return {
      title: labels.openArchiveTitle,
      description: labels.openArchiveDescription,
      cta: labels.openArchiveCta,
      onClick: () => onOpenSection(workflowStepToSection("archive")),
    };
  })();

  return (
    <ResearchNextAction
      eyebrow={labels.title}
      title={content.title}
      description={content.description}
      cta={content.cta}
      onClick={content.onClick}
      disabled={disabled}
    />
  );
}
