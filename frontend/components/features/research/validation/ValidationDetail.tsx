import Button from "@/components/ui/Button";
import type { Language } from "@/lib/i18n";
import type { ValidationStage } from "@/types/validation";
import DataConfidenceBadge from "./DataConfidenceBadge";
import EvidenceReferenceList from "./EvidenceReferenceList";
import ValidationGateTable, {
  type ValidationGateTableLabels,
} from "./ValidationGateTable";
import ValidationMetrics, {
  type ValidationMetricsLabels,
} from "./ValidationMetrics";
import ValidationStatusBadge from "./ValidationStatusBadge";

function formatDate(value: string | null, language: Language): string {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export type ValidationDetailLabels = {
  title: string;
  close: string;
  purpose: string;
  method: string;
  dataset: string;
  dateRange: string;
  benchmark: string;
  successCriteria: string;
  falsificationCriteria: string;
  result: string;
  dataConfidence: string;
  limitations: string;
  warnings: string;
  recommendation: string;
  runHistory: string;
  owner: string;
  lastRun: string;
  nextAction: string;
  none: string;
  gates: ValidationGateTableLabels;
  metrics: ValidationMetricsLabels;
  evidenceTitle: string;
  evidenceEmpty: string;
};

type ValidationDetailProps = {
  stage: ValidationStage;
  language: Language;
  labels: ValidationDetailLabels;
  onClose: () => void;
};

export default function ValidationDetail({
  stage,
  language,
  labels,
  onClose,
}: ValidationDetailProps) {
  return (
    <section className="validation-detail" aria-label={labels.title}>
      <header className="validation-detail__header">
        <div>
          <div className="validation-detail__badges">
            <ValidationStatusBadge status={stage.status} />
            <DataConfidenceBadge
              value={stage.dataConfidence}
              label={labels.dataConfidence}
            />
          </div>
          <h3 className="validation-detail__name">{stage.name}</h3>
        </div>
        <Button className="btn--ghost" onClick={onClose}>
          {labels.close}
        </Button>
      </header>

      <div className="validation-detail__grid">
        <section className="validation-detail__block">
          <h4>{labels.purpose}</h4>
          <p>{stage.purpose}</p>
          <h4>{labels.method}</h4>
          <p>{stage.method}</p>
          <dl className="validation-detail__dl">
            <div>
              <dt>{labels.dataset}</dt>
              <dd>{stage.dataset}</dd>
            </div>
            <div>
              <dt>{labels.dateRange}</dt>
              <dd className="font-mono">{stage.dateRange}</dd>
            </div>
            <div>
              <dt>{labels.benchmark}</dt>
              <dd>{stage.benchmark}</dd>
            </div>
            <div>
              <dt>{labels.owner}</dt>
              <dd>{stage.owner}</dd>
            </div>
            <div>
              <dt>{labels.lastRun}</dt>
              <dd>{formatDate(stage.lastRunAt, language)}</dd>
            </div>
          </dl>
        </section>

        <section className="validation-detail__block">
          <h4>{labels.successCriteria}</h4>
          <p>{stage.successCriteria}</p>
          <h4>{labels.falsificationCriteria}</h4>
          <p>{stage.falsificationCriteria}</p>
          <h4>{labels.result}</h4>
          <p>{stage.result}</p>
          <h4>{labels.recommendation}</h4>
          <p>{stage.recommendation}</p>
          <h4>{labels.nextAction}</h4>
          <p>{stage.nextAction}</p>
        </section>
      </div>

      <ValidationMetrics metrics={stage.metrics} labels={labels.metrics} />
      <ValidationGateTable gates={stage.gates} labels={labels.gates} />
      <EvidenceReferenceList
        refs={stage.evidenceRefs}
        title={labels.evidenceTitle}
        empty={labels.evidenceEmpty}
      />

      <section className="validation-detail__block">
        <h4>{labels.limitations}</h4>
        {stage.limitations.length === 0 ? (
          <p>{labels.none}</p>
        ) : (
          <ul>
            {stage.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
        <h4>{labels.warnings}</h4>
        {stage.warnings.length === 0 ? (
          <p>{labels.none}</p>
        ) : (
          <ul>
            {stage.warnings.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="validation-detail__block">
        <h4>{labels.runHistory}</h4>
        {stage.runHistory.length === 0 ? (
          <p>{labels.none}</p>
        ) : (
          <ul className="validation-detail__history">
            {stage.runHistory.map((item) => (
              <li key={item.id}>
                <span className="font-mono">
                  {formatDate(item.ranAt, language)}
                </span>
                {" · "}
                <ValidationStatusBadge status={item.outcome} />
                {" — "}
                {item.note}
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  );
}
