import type { Language } from "@/lib/i18n";
import type { EvaluationOverviewStats } from "@/types/evaluation";
import StatusBadge from "@/components/ui/StatusBadge";
import DataConfidenceBadge from "@/components/features/research/validation/DataConfidenceBadge";
import DemoDataBadge from "./DemoDataBadge";

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

function healthVariant(
  value: EvaluationOverviewStats["researchHealth"]
): "success" | "info" | "warning" | "danger" {
  switch (value) {
    case "Healthy":
      return "success";
    case "Watch":
      return "info";
    case "Degraded":
      return "warning";
    case "Blocked":
      return "danger";
  }
}

function readinessVariant(
  value: EvaluationOverviewStats["decisionReadiness"]
): "success" | "info" | "warning" | "danger" {
  switch (value) {
    case "Ready for Paper Trading":
    case "Ready for Evaluation Review":
      return "success";
    case "Continue Validation":
    case "Continue Research":
      return "info";
    case "Rework Required":
      return "danger";
    case "Archive Research":
      return "warning";
  }
}

export type ResearchConfidenceCardLabels = {
  title: string;
  score: string;
  level: string;
  disclaimer: string;
  demoLabel: string;
};

export type EvaluationOverviewLabels = {
  title: string;
  confidence: ResearchConfidenceCardLabels;
  researchHealth: string;
  decisionReadiness: string;
  recommendation: string;
  evaluationStatus: string;
  lastEvaluated: string;
  lifecycleStage: string;
  dataConfidence: string;
  blockers: string;
  evidenceCoverage: string;
};

type EvaluationOverviewProps = {
  stats: EvaluationOverviewStats;
  language: Language;
  labels: EvaluationOverviewLabels;
};

export default function EvaluationOverview({
  stats,
  language,
  labels,
}: EvaluationOverviewProps) {
  return (
    <section className="evaluation-overview" aria-label={labels.title}>
      <header className="evaluation-overview__header">
        <h3 className="evaluation-overview__title">{labels.title}</h3>
        <DemoDataBadge label={labels.confidence.demoLabel} />
      </header>

      <ResearchConfidenceCard stats={stats} labels={labels.confidence} />

      <dl className="evaluation-overview__grid">
        <div>
          <dt>{labels.researchHealth}</dt>
          <dd>
            <StatusBadge
              label={stats.researchHealth}
              variant={healthVariant(stats.researchHealth)}
            />
          </dd>
        </div>
        <div>
          <dt>{labels.decisionReadiness}</dt>
          <dd>
            <StatusBadge
              label={stats.decisionReadiness}
              variant={readinessVariant(stats.decisionReadiness)}
            />
          </dd>
        </div>
        <div>
          <dt>{labels.recommendation}</dt>
          <dd>{stats.recommendation}</dd>
        </div>
        <div>
          <dt>{labels.evaluationStatus}</dt>
          <dd>{stats.evaluationStatus}</dd>
        </div>
        <div>
          <dt>{labels.lastEvaluated}</dt>
          <dd>{formatDate(stats.lastEvaluatedAt, language)}</dd>
        </div>
        <div>
          <dt>{labels.lifecycleStage}</dt>
          <dd>{stats.lifecycleStage}</dd>
        </div>
        <div>
          <dt>{labels.dataConfidence}</dt>
          <dd>
            <DataConfidenceBadge value={stats.dataConfidence} />
          </dd>
        </div>
        <div>
          <dt>{labels.blockers}</dt>
          <dd className="font-mono">{stats.blockerCount}</dd>
        </div>
        <div>
          <dt>{labels.evidenceCoverage}</dt>
          <dd className="font-mono">{stats.evidenceCoveragePct}%</dd>
        </div>
      </dl>
    </section>
  );
}

function ResearchConfidenceCard({
  stats,
  labels,
}: {
  stats: EvaluationOverviewStats;
  labels: ResearchConfidenceCardLabels;
}) {
  return (
    <div className="research-confidence-card" aria-label={labels.title}>
      <div className="research-confidence-card__score-block">
        <p className="research-confidence-card__label">{labels.score}</p>
        <p className="research-confidence-card__score font-mono">
          {stats.confidenceScore}
        </p>
        <p className="research-confidence-card__level">
          {labels.level}: {stats.confidenceLevel}
        </p>
      </div>
      <p className="research-confidence-card__disclaimer">{labels.disclaimer}</p>
    </div>
  );
}
