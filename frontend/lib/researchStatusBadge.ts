/**
 * Canonical lifecycle badge vocabulary for research workspace surfaces.
 * Presentation-only — does not invent status from data.
 */

export type ResearchBadgeVariant =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger";

/** Canonical status tokens used in matrices and summaries. */
export type CanonicalResearchStatus =
  | "completed"
  | "pending"
  | "planned"
  | "blocked"
  | "active"
  | "not_started"
  | "approved"
  | "rejected";

export function canonicalStatusVariant(
  status: CanonicalResearchStatus | string
): ResearchBadgeVariant {
  switch (status) {
    case "completed":
    case "approved":
    case "active":
    case "configured":
    case "eligible":
      return "success";
    case "pending":
    case "needs_review":
    case "under_review":
    case "in_progress":
    case "incomplete":
      return "warning";
    case "blocked":
    case "rejected":
    case "failed":
    case "not_eligible":
    case "stopped":
      return "danger";
    case "planned":
    case "not_started":
    case "not_ready":
    case "unavailable":
    case "archived":
    default:
      return "neutral";
  }
}
