import EmptyState from "@/components/ui/EmptyState";

export default function EvaluationEmptyState({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return <EmptyState title={title} description={description} />;
}
