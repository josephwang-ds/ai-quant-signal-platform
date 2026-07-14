type ConfidenceBadgeProps = {
  /** 0–100；null = pending / not calculated */
  score: number | null;
  label?: string;
  pendingLabel?: string;
};

function clampScore(score: number): number {
  if (Number.isNaN(score)) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round(score)));
}

function confidenceTone(score: number): "low" | "mid" | "high" {
  if (score >= 65) {
    return "high";
  }
  if (score >= 40) {
    return "mid";
  }
  return "low";
}

/**
 * 研究置信度展示：分数 + 轻量进度条。
 * null score shows a pending state — never invent a numeric confidence.
 */
export default function ConfidenceBadge({
  score,
  label = "Confidence",
  pendingLabel = "Pending",
}: ConfidenceBadgeProps) {
  if (score === null) {
    return (
      <div
        className="confidence-badge confidence-badge--pending"
        title={`${label}: ${pendingLabel}`}
      >
        <div className="confidence-badge__meta">
          <span className="confidence-badge__label">{label}</span>
          <span className="confidence-badge__score font-mono">{pendingLabel}</span>
        </div>
        <div
          className="confidence-badge__track"
          role="meter"
          aria-label={label}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuetext={pendingLabel}
        >
          <span className="confidence-badge__fill" style={{ width: "0%" }} />
        </div>
      </div>
    );
  }

  const value = clampScore(score);
  const tone = confidenceTone(value);

  return (
    <div
      className={`confidence-badge confidence-badge--${tone}`}
      title={`${label}: ${value}`}
    >
      <div className="confidence-badge__meta">
        <span className="confidence-badge__label">{label}</span>
        <span className="confidence-badge__score font-mono">{value}</span>
      </div>
      <div
        className="confidence-badge__track"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
      >
        <span className="confidence-badge__fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
