import type { Language } from "@/lib/i18n";
import type { ValidationStage } from "@/types/validation";
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

export type ValidationStageCardLabels = {
  purpose: string;
  lastRun: string;
  owner: string;
  evidence: string;
  keyResult: string;
  warnings: string;
  nextAction: string;
  openDetail: string;
};

type ValidationStageCardProps = {
  stage: ValidationStage;
  language: Language;
  labels: ValidationStageCardLabels;
  selected?: boolean;
  onSelect: (id: string) => void;
};

export default function ValidationStageCard({
  stage,
  language,
  labels,
  selected = false,
  onSelect,
}: ValidationStageCardProps) {
  return (
    <article
      className={`validation-stage-card${selected ? " is-selected" : ""}`}
      role="article"
    >
      <header className="validation-stage-card__header">
        <div>
          <div className="validation-stage-card__badges">
            <ValidationStatusBadge status={stage.status} />
          </div>
          <h3 className="validation-stage-card__name">{stage.name}</h3>
        </div>
        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => onSelect(stage.id)}
        >
          {labels.openDetail}
        </button>
      </header>

      <p className="validation-stage-card__purpose">
        <span className="validation-stage-card__label">{labels.purpose}</span>
        {stage.purpose}
      </p>

      <dl className="validation-stage-card__meta">
        <div>
          <dt>{labels.lastRun}</dt>
          <dd>{formatDate(stage.lastRunAt, language)}</dd>
        </div>
        <div>
          <dt>{labels.owner}</dt>
          <dd>{stage.owner}</dd>
        </div>
        <div>
          <dt>{labels.evidence}</dt>
          <dd className="font-mono">{stage.evidenceCount}</dd>
        </div>
      </dl>

      <p className="validation-stage-card__result">
        <span className="validation-stage-card__label">{labels.keyResult}</span>
        {stage.keyResult}
      </p>

      {stage.warnings.length > 0 ? (
        <p className="validation-stage-card__warnings">
          <span className="validation-stage-card__label">{labels.warnings}</span>
          {stage.warnings.join(" · ")}
        </p>
      ) : null}

      <p className="validation-stage-card__next">
        <span className="validation-stage-card__label">{labels.nextAction}</span>
        {stage.nextAction}
      </p>
    </article>
  );
}
