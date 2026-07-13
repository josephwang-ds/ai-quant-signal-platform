import type { ExperimentStatus } from "@/types/experiment";
import StatusBadge from "@/components/ui/StatusBadge";

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
}: {
  status: ExperimentStatus;
}) {
  return <StatusBadge label={status} variant={statusVariant(status)} />;
}
