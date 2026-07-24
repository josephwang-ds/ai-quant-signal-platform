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
import type {
  FactorValidationResult,
  FactorValidationStatus,
} from "@/types/factorValidation";

export type DecisionTabProps = {
  section: Extract<ResearchWorkspaceSection, "paper" | "decision">;
  language: Language;
  tr: (key: TranslationKey) => string;
  research: ResearchDetail | null;
  validationStatus: ResearchValidationStatus;
  validation: ResearchValidationResult | null;
  evaluationStatus: ResearchEvaluationRequestStatus;
  evaluation: ResearchEvaluationResult | null;
  factorValidationStatus?: FactorValidationStatus;
  factorValidation?: FactorValidationResult | null;
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
  factorValidationStatus = "idle",
  factorValidation = null,
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

  const factorReady =
    factorValidationStatus === "ready" &&
    Boolean(factorValidation) &&
    (factorValidation?.validation_status === "completed" ||
      (factorValidation?.ic.summary.n_periods ?? 0) > 0);

  return (
    <ResearchDecisionCenter
      research={research}
      validation={validationStatus === "ready" ? validation : null}
      evaluation={evaluationStatus === "ready" ? evaluation : null}
      factorValidationCompleted={factorReady}
      evidenceTimestamp={
        factorValidation?.generated_at ??
        (validationStatus === "ready" ? validation?.generated_at : null) ??
        null
      }
      labels={buildDecisionCenterLabels(tr)}
    />
  );
}
