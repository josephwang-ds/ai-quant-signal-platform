import type { BacktestRunSummary } from "@/types/market";
import type { Language, TranslationKey } from "@/lib/i18n";
import { getDrawdownMetric } from "@/lib/experimentCompare";
import {
  formatMetricPercent,
  formatMetricSharpe,
} from "@/lib/formatters";
import { translateStrategyName } from "@/lib/i18n";

function formatCreatedAt(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatRunId(runId: string): string {
  return runId.slice(0, 8);
}

function getExperimentTradeCount(run: BacktestRunSummary): number {
  return run.trade_count ?? run.metrics?.number_of_trades ?? 0;
}

function runTitle(run: BacktestRunSummary): string {
  const note = run.notes?.trim();
  if (note) {
    return note.length > 32 ? `${note.slice(0, 32)}…` : note;
  }
  return formatRunId(run.id);
}

export type ExperimentRunCardProps = {
  run: BacktestRunSummary;
  language: Language;
  selected: boolean;
  compareSelected: boolean;
  tr: (key: TranslationKey) => string;
  onSelect: () => void;
  onToggleCompare: () => void;
};

export function ExperimentRunCard({
  run,
  language,
  selected,
  compareSelected,
  tr,
  onSelect,
  onToggleCompare,
}: ExperimentRunCardProps) {
  const strategyLabel = translateStrategyName(language, run.strategy);

  return (
    <article
      className={[
        "experiment-run-card",
        selected ? "experiment-run-card--selected" : "",
        compareSelected ? "experiment-run-card--compare" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onClick={onSelect}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect();
        }
      }}
      role="button"
      tabIndex={0}
    >
      <label
        className="experiment-run-card__check"
        onClick={(event) => event.stopPropagation()}
      >
        <input
          type="checkbox"
          checked={compareSelected}
          onChange={onToggleCompare}
          aria-label={`compare-${run.id}`}
        />
      </label>

      <div className="experiment-run-card__body">
        <p className="experiment-run-card__title">
          <span className="experiment-run-card__name">{runTitle(run)}</span>
          <span className="experiment-run-card__dot">·</span>
          <span>{run.ticker}</span>
          <span className="experiment-run-card__dot">·</span>
          <span>{strategyLabel}</span>
        </p>
        <p className="experiment-run-card__meta">
          <span>{formatCreatedAt(run.created_at, language)}</span>
          <span className="experiment-run-card__dot">·</span>
          <span className="font-mono">{formatRunId(run.id)}</span>
        </p>
      </div>

      <div className="experiment-run-card__metrics font-mono">
        <span className="experiment-run-card__metric">
          {formatMetricPercent(run.metrics?.total_return ?? null)}
        </span>
        <span className="experiment-run-card__metric">
          Sharpe {formatMetricSharpe(run.metrics?.sharpe_ratio ?? null)}
        </span>
        <span className="experiment-run-card__metric">
          {formatMetricPercent(getDrawdownMetric(run))}
        </span>
        <span className="experiment-run-card__metric">
          {getExperimentTradeCount(run)} {tr("experimentsTradeCount")}
        </span>
      </div>
    </article>
  );
}
