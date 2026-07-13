import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";

type ExperimentEmptyStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: "catalog" | "filter";
};

export default function ExperimentEmptyState({
  title,
  description,
  actionLabel,
  onAction,
  variant = "catalog",
}: ExperimentEmptyStateProps) {
  return (
    <EmptyState
      title={title}
      description={description}
      action={
        variant === "catalog" && actionLabel && onAction ? (
          <Button primary onClick={onAction}>
            {actionLabel}
          </Button>
        ) : undefined
      }
    />
  );
}
