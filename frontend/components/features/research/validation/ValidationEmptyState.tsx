import EmptyState from "@/components/ui/EmptyState";

type ValidationEmptyStateProps = {
  title: string;
  description: string;
  variant?: "catalog" | "filter";
};

export default function ValidationEmptyState({
  title,
  description,
}: ValidationEmptyStateProps) {
  return <EmptyState title={title} description={description} />;
}
