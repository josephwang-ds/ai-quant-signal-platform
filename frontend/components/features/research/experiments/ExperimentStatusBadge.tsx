import type { ExperimentStatus } from "@/types/experiment";
import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import { experimentStatusLabel } from "@/lib/researchDisplay";

function statusVariant(
  status: ExperimentStatus
): "neutral" | "info" | "success" | "warning" | "danger" {
  switch (status) {
    case "Designed":
      return "neutral";
    case "Approved":
      return "info";
    case "Running":
      return "warning";
    case "Completed":
      return "success";
    case "Failed":
    case "Invalidated":
      return "danger";
    default:
      return "neutral";
  }
}

export default function ExperimentStatusBadge({
  status,
  language,
}: {
  status: ExperimentStatus;
  language: Language;
}) {
  return <StatusBadge label={experimentStatusLabel(status, language)} variant={statusVariant(status)} />;
}
