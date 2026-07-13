import StatusBadge from "@/components/ui/StatusBadge";

function confidenceVariant(
  value: "high" | "medium" | "low" | "degraded"
): "success" | "info" | "warning" | "danger" {
  switch (value) {
    case "high":
      return "success";
    case "medium":
      return "info";
    case "low":
      return "warning";
    case "degraded":
      return "danger";
  }
}

export default function DataConfidenceBadge({
  value,
  label,
}: {
  value: "high" | "medium" | "low" | "degraded";
  label?: string;
}) {
  return (
    <StatusBadge
      label={label ? `${label}: ${value}` : value}
      variant={confidenceVariant(value)}
    />
  );
}
