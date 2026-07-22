import type { MetricTone } from "@/lib/formatters";

type MetricSummaryCardProps = {
  label: string;
  value: string;
  description?: string;
  tone?: MetricTone | "emphasis";
};

/**
 * 工作区摘要指标卡：轻量、非交易仪表盘风格。
 * 与 MetricCard 并存；专用于 Research Overview 叙述性指标。
 */
export default function MetricSummaryCard({
  label,
  value,
  description,
  tone = "default",
}: MetricSummaryCardProps) {
  const valueToneClass =
    tone === "positive"
      ? "metric-summary-card__value--positive"
      : tone === "negative"
        ? "metric-summary-card__value--negative"
        : tone === "accent"
          ? "metric-summary-card__value--accent"
          : "";

  const cardClass = `metric-summary-card${
    tone === "emphasis" ? " metric-summary-card--emphasis" : ""
  }`;

  return (
    <div className={cardClass}>
      <p className="metric-summary-card__label">{label}</p>
      <p className={`metric-summary-card__value ${valueToneClass}`.trim()}>
        {value}
      </p>
      {description ? (
        <p className="metric-summary-card__description">{description}</p>
      ) : null}
    </div>
  );
}
