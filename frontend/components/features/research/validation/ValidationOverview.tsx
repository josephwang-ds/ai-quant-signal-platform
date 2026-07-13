import type { Language } from "@/lib/i18n";
import type { ValidationOverviewStats } from "@/types/validation";
import StatusBadge from "@/components/ui/StatusBadge";
import ValidationStatusBadge from "./ValidationStatusBadge";

function formatDate(value: string | null, language: Language): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function readinessVariant(
  readiness: ValidationOverviewStats["readiness"]
): "success" | "warning" | "danger" | "info" {
  switch (readiness) {
    case "Ready for Evaluation":
      return "success";
    case "Continue Validation":
      return "info";
    case "Insufficient Evidence":
      return "warning";
    case "Blocked":
      return "danger";
  }
}

export type ValidationOverviewLabels = {
  title: string;
  overallStatus: string;
  completed: string;
  passed: string;
  failed: string;
  inconclusive: string;
  blocking: string;
  lastValidation: string;
  readiness: string;
  readinessNote: string;
};

type ValidationOverviewProps = {
  stats: ValidationOverviewStats;
  language: Language;
  labels: ValidationOverviewLabels;
};

export default function ValidationOverview({
  stats,
  language,
  labels,
}: ValidationOverviewProps) {
  return (
    <section className="validation-overview" aria-label={labels.title}>
      <header className="validation-overview__header">
        <h3 className="validation-overview__title">{labels.title}</h3>
        <p className="section-meta">{labels.readinessNote}</p>
      </header>

      <div className="validation-overview__readiness">
        <span className="validation-overview__label">{labels.readiness}</span>
        <StatusBadge
          label={stats.readiness}
          variant={readinessVariant(stats.readiness)}
        />
      </div>

      <dl className="validation-overview__grid">
        <div>
          <dt>{labels.overallStatus}</dt>
          <dd>
            <ValidationStatusBadge status={stats.overallStatus} />
          </dd>
        </div>
        <div>
          <dt>{labels.completed}</dt>
          <dd className="font-mono">{stats.completedCount}</dd>
        </div>
        <div>
          <dt>{labels.passed}</dt>
          <dd className="font-mono">{stats.passedCount}</dd>
        </div>
        <div>
          <dt>{labels.failed}</dt>
          <dd className="font-mono">{stats.failedCount}</dd>
        </div>
        <div>
          <dt>{labels.inconclusive}</dt>
          <dd className="font-mono">{stats.inconclusiveCount}</dd>
        </div>
        <div>
          <dt>{labels.blocking}</dt>
          <dd className="font-mono">{stats.blockingCount}</dd>
        </div>
        <div>
          <dt>{labels.lastValidation}</dt>
          <dd>{formatDate(stats.lastValidationAt, language)}</dd>
        </div>
      </dl>
    </section>
  );
}
