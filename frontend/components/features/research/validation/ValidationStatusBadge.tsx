import StatusBadge from "@/components/ui/StatusBadge";
import type { ValidationStatus } from "@/types/validation";

function statusVariant(
  status: ValidationStatus | "Mixed"
): "neutral" | "info" | "success" | "warning" | "danger" {
  switch (status) {
    case "Not Started":
      return "neutral";
    case "Ready":
      return "info";
    case "Running":
      return "warning";
    case "Passed":
      return "success";
    case "Failed":
    case "Invalidated":
      return "danger";
    case "Inconclusive":
    case "Mixed":
      return "warning";
    default:
      return "neutral";
  }
}

export default function ValidationStatusBadge({
  status,
}: {
  status: ValidationStatus | "Mixed";
}) {
  return <StatusBadge label={status} variant={statusVariant(status)} />;
}
