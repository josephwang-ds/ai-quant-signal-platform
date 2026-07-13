import StatusBadge from "@/components/ui/StatusBadge";
import type { EvaluationDimensionStatus } from "@/types/evaluation";

function statusVariant(
  status: EvaluationDimensionStatus
): "success" | "info" | "warning" | "danger" | "neutral" {
  switch (status) {
    case "Strong":
      return "success";
    case "Acceptable":
      return "info";
    case "Weak":
    case "Inconclusive":
      return "warning";
    case "Failed":
      return "danger";
    case "Missing":
    default:
      return "neutral";
  }
}

export default function EvaluationDimensionStatusBadge({
  status,
}: {
  status: EvaluationDimensionStatus;
}) {
  return <StatusBadge label={status} variant={statusVariant(status)} />;
}
