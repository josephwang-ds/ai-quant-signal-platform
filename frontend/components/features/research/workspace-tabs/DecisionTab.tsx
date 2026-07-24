"use client";

import ResearchPaperTradingCenter from "@/components/features/research/paper/ResearchPaperTradingCenter";
import ResearchDecisionCenter from "@/components/features/research/decision/ResearchDecisionCenter";
import { buildPaperTradingLabels } from "@/components/features/paper-trading/PaperTradingPage";
import { buildDecisionCenterLabels } from "@/lib/decisionCenterLabels";
import type { Language, TranslationKey } from "@/lib/i18n";
import type { ResearchDetail, ResearchWorkspaceSection } from "@/types/research";
import type {
  ResearchValidationResult,
  ResearchValidationStatus,
} from "@/types/researchValidation";
import type {
  ResearchEvaluationResult,
  ResearchEvaluationRequestStatus,
} from "@/types/researchEvaluation";

export type DecisionTabProps = {
  section: Extract<ResearchWorkspaceSection, "paper" | "decision">;
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
  tr,
  research,
  validationStatus,
  validation,
  evaluationStatus,
  evaluation,
  navigateToSection,
}: DecisionTabProps) {
  if (!research) return null;

  if (section === "paper") {
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

  return (
    <ResearchDecisionCenter
      research={research}
      validation={validationStatus === "ready" ? validation : null}
      evaluation={evaluationStatus === "ready" ? evaluation : null}
      labels={buildDecisionCenterLabels(tr)}
    />
  );
}
