"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import ResearchPaperTradingCenter from "@/components/features/research/paper/ResearchPaperTradingCenter";
import ResearchDecisionCenter from "@/components/features/research/decision/ResearchDecisionCenter";
import { buildPaperTradingLabels } from "@/components/features/paper-trading/PaperTradingPage";
import { buildDecisionCenterLabels } from "@/lib/decisionCenterLabels";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchDetail, ResearchWorkspaceSection } from "@/types/research";
import type { ResearchValidationResult } from "@/types/researchValidation";
import type { ResearchValidationStatus } from "@/types/researchValidation";
import type { ResearchEvaluationResult, ResearchEvaluationRequestStatus } from "@/types/researchEvaluation";
import { PLACEHOLDER_COPY } from "./placeholderCopy";

export type DecisionTabProps = {
  section: Extract<ResearchWorkspaceSection, "paper" | "decision" | "archive">;
  language: Language;
  tr: (key: TranslationKey) => string;
  research: ResearchDetail | null;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  navigateToSection: (section: ResearchWorkspaceSection) => void;
};

export default function DecisionTab({
  section,
  language,
  tr,
  research,
  validationStatus,
  validation,
  evaluationStatus,
  evaluation,
  navigateToSection,
}: DecisionTabProps) {
  if (section === "paper" && research) {
    return (
      <ResearchPaperTradingCenter
        research={research}
        validation={validationStatus === "ready" ? validation : null}
        evaluation={evaluationStatus === "ready" ? evaluation : null}
        labels={buildPaperTradingLabels(tr)}
        onContinue={() => navigateToSection("decision")}
      />
    );

  }

  if (section === "decision" && research) {
    return (
      <ResearchDecisionCenter
        research={research}
        validation={validationStatus === "ready" ? validation : null}
        evaluation={evaluationStatus === "ready" ? evaluation : null}
        labels={buildDecisionCenterLabels(tr)}
        onContinue={() => navigateToSection("archive")}
      />
    );

  }

  if (section === "archive") {
    const copy = PLACEHOLDER_COPY.archive;
    return (
      <WorkspacePlaceholder
        title={tr(copy.titleKey)}
        summary={tr(copy.summaryKey)}
        plannedCapabilities={copy.capabilityKeys.map((key) => tr(key))}
        deferredNote={tr("researchWsDeferredNote")}
        emptyTitle={tr("researchWsDeferredEmptyTitle")}
        capabilitiesCaption={tr("researchWsPlannedCapabilities")}
      />
    );
  }

  return null;
}
