import type { ExperimentType } from "@/types/experiment";

export default function ExperimentTypeBadge({
  experimentType,
}: {
  experimentType: ExperimentType;
}) {
  return <span className="experiment-type-badge">{experimentType}</span>;
}
