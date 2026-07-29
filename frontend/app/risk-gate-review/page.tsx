import { permanentRedirect } from "next/navigation";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";

/**
 * Standalone Risk Gate Review form is retired.
 * Pressure-test / robustness evidence lives on the canonical study workspace.
 */
export default function RiskGateReviewPage() {
  permanentRedirect(
    `/engine/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}?tab=robustness`
  );
}
