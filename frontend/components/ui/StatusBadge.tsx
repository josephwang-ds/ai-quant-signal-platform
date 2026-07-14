type StatusBadgeVariant =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger"
  | "bullish"
  | "bearish"
  | "buy"
  | "sell";

type StatusBadgeProps = {
  label: string;
  variant?: StatusBadgeVariant;
};

export default function StatusBadge({ label, variant = "neutral" }: StatusBadgeProps) {
  return <span className={`badge badge--${variant}`}>{label}</span>;
}

export function signalLabelVariant(label: string): StatusBadgeVariant {
  switch (label) {
    case "Strong Bullish Watchlist":
    case "Bullish Watchlist":
      return "bullish";
    case "Bearish Watchlist":
      return "bearish";
    case "High Risk / Avoid":
      return "danger";
    case "Neutral":
      return "neutral";
    default:
      return "neutral";
  }
}

export function trendVariant(trend: "Positive" | "Mixed" | "Weak"): StatusBadgeVariant {
  switch (trend) {
    case "Positive":
      return "success";
    case "Mixed":
      return "warning";
    case "Weak":
      return "danger";
  }
}

export function riskVariant(risk: "High" | "Medium" | "Low"): StatusBadgeVariant {
  switch (risk) {
    case "High":
      return "danger";
    case "Medium":
      return "warning";
    case "Low":
      return "success";
  }
}

export function passFailVariant(passed: boolean): StatusBadgeVariant {
  return passed ? "success" : "danger";
}

export function healthVariant(status: string): StatusBadgeVariant {
  return status === "ok" ? "success" : "danger";
}

/** Research 生命周期状态 → 徽标色调（对齐 Ch3 状态机）。 */
export function researchLifecycleVariant(status: string): StatusBadgeVariant {
  switch (status) {
    case "Draft":
      return "neutral";
    case "Data Integration":
      return "info";
    case "Running":
      return "info";
    case "Review":
      return "warning";
    case "Validated":
      return "success";
    case "Paper Trading":
      return "buy";
    case "Monitoring":
      return "bullish";
    case "Archived":
      return "neutral";
    default:
      return "neutral";
  }
}
