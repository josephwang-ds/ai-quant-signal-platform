import type { ExperimentType } from "@/types/experiment";
import type { Language } from "@/lib/i18n";
import { experimentTypeLabel } from "@/lib/researchDisplay";

export default function ExperimentTypeBadge({
  experimentType,
  language,
}: {
  experimentType: ExperimentType;
  language: Language;
}) {
  return <span className="experiment-type-badge">{experimentTypeLabel(experimentType, language)}</span>;
}
