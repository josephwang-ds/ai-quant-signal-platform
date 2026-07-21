/**
 * Pure helpers for Research Workspace action-rail triggers (PR-020).
 *
 * Duplicate-request prevention:
 * - First visit to Validation/Evaluation: navigate only; the existing tab hook
 *   owns the single auto-fetch when its section becomes active.
 * - Already on an evidence-active section: call the existing reload() once.
 */

export function shouldReloadValidationOnAction(
  validationEvidenceActive: boolean
): boolean {
  return validationEvidenceActive;
}

export function shouldReloadEvaluationOnAction(
  validationRunId: string | null,
  activeSection: string
): boolean {
  // Evidence tab owns validation + evaluation; evaluation URL still maps here.
  return (
    Boolean(validationRunId) &&
    (activeSection === "validation" || activeSection === "evaluation")
  );
}

export function canRequestEvaluation(validationRunId: string | null): boolean {
  return Boolean(validationRunId);
}
