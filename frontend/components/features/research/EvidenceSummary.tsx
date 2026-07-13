import StatusBadge from "@/components/ui/StatusBadge";
import type { ResearchEvidenceItem } from "@/types/research";

function evidenceVariant(
  status: ResearchEvidenceItem["status"]
): "success" | "info" | "warning" | "neutral" | "danger" {
  switch (status) {
    case "completed":
      return "success";
    case "in_progress":
      return "info";
    case "blocked":
      return "danger";
    case "pending":
    default:
      return "warning";
  }
}

function evidenceStatusLabel(status: ResearchEvidenceItem["status"]): string {
  switch (status) {
    case "completed":
      return "Completed";
    case "in_progress":
      return "In progress";
    case "blocked":
      return "Blocked";
    case "pending":
    default:
      return "Pending";
  }
}

export type EvidenceSummaryProps = {
  items: ResearchEvidenceItem[];
  title?: string;
  description?: string;
};

/** Evidence 摘要列表：状态 + 简洁结果，非图表墙。 */
export default function EvidenceSummary({
  items,
  title = "Evidence summary",
  description,
}: EvidenceSummaryProps) {
  return (
    <section className="evidence-summary" aria-label={title}>
      <header className="evidence-summary__header">
        <h3 className="evidence-summary__title">{title}</h3>
        {description ? (
          <p className="evidence-summary__description">{description}</p>
        ) : null}
      </header>
      <ul className="evidence-summary__list">
        {items.map((item) => (
          <li key={item.id} className="evidence-summary__item">
            <div className="evidence-summary__item-head">
              <span className="evidence-summary__item-label">{item.label}</span>
              <StatusBadge
                label={evidenceStatusLabel(item.status)}
                variant={evidenceVariant(item.status)}
              />
            </div>
            <p className="evidence-summary__item-result">{item.result}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
