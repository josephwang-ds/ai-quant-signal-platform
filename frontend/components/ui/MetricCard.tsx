import type { MetricTone } from "@/lib/formatters";

type MetricCardProps = {
  label: string;
  value: string;
  description?: string;
  featured?: boolean;
  tone?: MetricTone;
};

export default function MetricCard({
  label,
  value,
  description,
  featured = false,
  tone = "default",
}: MetricCardProps) {
  const toneClass =
    tone === "positive"
      ? "metric-card__value--positive"
      : tone === "negative"
        ? "metric-card__value--negative"
        : tone === "accent"
          ? "metric-card__value--accent"
          : "";

  const cardClass = `metric-card${featured ? " metric-card--featured" : ""}`;

  return (
    <div className={cardClass}>
      <p className="metric-card__label">{label}</p>
      <p className={`metric-card__value ${toneClass}`.trim()}>{value}</p>
      {description ? <p className="metric-card__description">{description}</p> : null}
    </div>
  );
}
