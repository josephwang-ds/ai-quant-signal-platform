"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import ResearchRobustnessCenter from "@/components/features/research/robustness/ResearchRobustnessCenter";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { useResearchEvaluation } from "@/components/features/research/evaluation/useResearchEvaluation";
import { useResearchValidation } from "@/components/features/research/validation/useResearchValidation";
import { buildRobustnessCenterLabels } from "@/lib/robustnessCenterLabels";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/**
 * Standalone Robustness Center entry.
 * Organises robustness work for the canonical research — no new quant engine.
 */
export default function RobustnessPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const {
    enabled: validationEnabled,
    status: validationStatus,
    validation,
    error: validationError,
  } = useResearchValidation(CANONICAL_RESEARCH_ID, true);
  const validationRunId = validation?.validation_run_id ?? null;
  const {
    status: evaluationStatus,
    evaluation,
  } = useResearchEvaluation(CANONICAL_RESEARCH_ID, true, validationRunId);

  const labels = buildRobustnessCenterLabels(tr);

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <p className="section-meta">{tr("robustnessCanonicalHint")}</p>
        <p className="section-meta">
          <Link
            href={`/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}?tab=robustness`}
            className="btn btn--ghost"
          >
            {tr("robustnessOpenWorkspace")}
          </Link>
        </p>
      </SectionCard>

      {validationEnabled && validationStatus === "loading" ? (
        <SectionCard>
          <LoadingState message={tr("researchValLoading")} />
        </SectionCard>
      ) : null}

      {validationEnabled && validationStatus === "error" ? (
        <SectionCard>
          <ErrorAlert
            title={tr("researchValUnavailableTitle")}
            message={validationError ?? tr("researchValUnavailableDescription")}
          />
        </SectionCard>
      ) : null}

      {validationStatus === "ready" || evaluationStatus === "ready" || !validationEnabled ? (
        <SectionCard>
          <ResearchRobustnessCenter
            validation={validationStatus === "ready" ? validation : null}
            evaluation={evaluationStatus === "ready" ? evaluation : null}
            labels={labels}
          />
        </SectionCard>
      ) : null}
    </AppShell>
  );
}
