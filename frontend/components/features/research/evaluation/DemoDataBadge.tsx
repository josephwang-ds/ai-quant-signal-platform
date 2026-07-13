import StatusBadge from "@/components/ui/StatusBadge";

/** Restrained demo/simulated data label for research surfaces. */
export default function DemoDataBadge({
  label = "Simulated Evaluation",
}: {
  label?: string;
}) {
  return <StatusBadge label={label} variant="neutral" />;
}
