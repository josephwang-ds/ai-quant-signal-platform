import StatusBadge from "@/components/ui/StatusBadge";
import {
  formatMetricPercent,
  formatMetricSharpe,
  formatMetricTrades,
} from "@/lib/formatters";
import { canonicalStatusVariant } from "@/lib/researchStatusBadge";
import type { WalkForwardResultView } from "@/lib/researchRobustness";

export type WalkForwardResultCardLabels = {
  title: string;
  notRun: string;
  notRunNote: string;
  scheme: string;
  folds: string;
  methodology: string;
  protocolHash: string;
  reason: string;
  aggregateTitle: string;
  completedFolds: string;
  positiveReturnRatio: string;
  outperformRatio: string;
  medianReturn: string;
  medianSharpe: string;
  worstDrawdown: string;
  foldTableTitle: string;
  fold: string;
  train: string;
  oos: string;
  strategyReturn: string;
  benchmarkReturn: string;
  sharpe: string;
  maxDrawdown: string;
  trades: string;
  status: string;
  checksTitle: string;
  limitationsTitle: string;
  thresholdsNote: string;
};

type Props = {
  walkForward: WalkForwardResultView;
  labels: WalkForwardResultCardLabels;
};

function formatRatio(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(1)}%`;
}

function formatPct(value: number | null | undefined): string {
  const formatted = formatMetricPercent(value);
  return formatted === "N/A" ? "n/a" : formatted;
}

function formatSharpe(value: number | null | undefined): string {
  const formatted = formatMetricSharpe(value);
  return formatted === "N/A" ? "n/a" : formatted;
}

function formatTrades(value: number | null | undefined): string {
  const formatted = formatMetricTrades(value);
  return formatted === "N/A" ? "n/a" : formatted;
}

function toneForRunState(runState: WalkForwardResultView["runState"]): string {
  if (runState === "completed") return "completed";
  if (runState === "failed") return "blocked";
  if (runState === "incomplete" || runState === "unavailable") return "pending";
  return "not_started";
}

/**
 * Displays backend walk-forward evidence only. Does not apply pass/fail
 * thresholds in the client — checks are rendered from the validation payload.
 */
export default function WalkForwardResultCard({ walkForward, labels }: Props) {
  if (walkForward.runState === "not_run") {
    return (
      <div className="research-status-block" data-testid="walk-forward-result-card">
        <StatusBadge
          label={labels.notRun}
          variant={canonicalStatusVariant("not_started")}
        />
        <p className="research-status-block__body">{labels.notRunNote}</p>
      </div>
    );
  }

  const aggregate = walkForward.aggregate;

  return (
    <div className="research-status-block" data-testid="walk-forward-result-card">
      <div className="research-key-value-list" style={{ marginBottom: "0.75rem" }}>
        <StatusBadge
          label={walkForward.statusLabel}
          variant={canonicalStatusVariant(toneForRunState(walkForward.runState))}
        />
      </div>

      <dl className="research-key-value-list">
        <div>
          <dt>{labels.scheme}</dt>
          <dd>{walkForward.scheme ?? "n/a"}</dd>
        </div>
        <div>
          <dt>{labels.folds}</dt>
          <dd>{walkForward.nFolds ?? "n/a"}</dd>
        </div>
        <div>
          <dt>{labels.methodology}</dt>
          <dd>
            {walkForward.methodologyId
              ? `${walkForward.methodologyId} ${walkForward.methodologyVersion ?? ""}`.trim()
              : "n/a"}
          </dd>
        </div>
        <div>
          <dt>{labels.protocolHash}</dt>
          <dd>
            {walkForward.protocolHash
              ? `${walkForward.protocolHash.slice(0, 12)}…`
              : "n/a"}
          </dd>
        </div>
      </dl>

      {walkForward.reason ? (
        <p className="research-status-block__body">
          <strong>{labels.reason}:</strong> {walkForward.reason}
          {walkForward.reasonCode ? ` (${walkForward.reasonCode})` : ""}
        </p>
      ) : null}

      <p className="research-status-block__body">{labels.thresholdsNote}</p>

      {aggregate ? (
        <>
          <h4 className="research-subsection-title">{labels.aggregateTitle}</h4>
          <dl className="research-key-value-list">
            <div>
              <dt>{labels.completedFolds}</dt>
              <dd>
                {aggregate.completed_fold_count ?? "n/a"}
                {aggregate.requested_fold_count != null
                  ? ` / ${aggregate.requested_fold_count}`
                  : ""}
              </dd>
            </div>
            <div>
              <dt>{labels.positiveReturnRatio}</dt>
              <dd>{formatRatio(aggregate.positive_return_fold_ratio)}</dd>
            </div>
            <div>
              <dt>{labels.outperformRatio}</dt>
              <dd>{formatRatio(aggregate.benchmark_outperformance_fold_ratio)}</dd>
            </div>
            <div>
              <dt>{labels.medianReturn}</dt>
              <dd>{formatPct(aggregate.median_oos_return)}</dd>
            </div>
            <div>
              <dt>{labels.medianSharpe}</dt>
              <dd>{formatSharpe(aggregate.median_oos_sharpe)}</dd>
            </div>
            <div>
              <dt>{labels.worstDrawdown}</dt>
              <dd>{formatPct(aggregate.worst_oos_drawdown)}</dd>
            </div>
          </dl>
        </>
      ) : null}

      {walkForward.folds.length > 0 ? (
        <>
          <h4 className="research-subsection-title">{labels.foldTableTitle}</h4>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>{labels.fold}</th>
                  <th>{labels.status}</th>
                  <th>{labels.train}</th>
                  <th>{labels.oos}</th>
                  <th>{labels.strategyReturn}</th>
                  <th>{labels.benchmarkReturn}</th>
                  <th>{labels.sharpe}</th>
                  <th>{labels.maxDrawdown}</th>
                  <th>{labels.trades}</th>
                </tr>
              </thead>
              <tbody>
                {walkForward.folds.map((fold) => (
                  <tr key={fold.fold_index}>
                    <td>{fold.fold_index + 1}</td>
                    <td>
                      {fold.status}
                      {fold.failure_reason ? ` — ${fold.failure_reason}` : ""}
                    </td>
                    <td>
                      {fold.train_start ?? "n/a"} → {fold.train_end ?? "n/a"}
                    </td>
                    <td>
                      {fold.oos_start ?? "n/a"} → {fold.oos_end ?? "n/a"}
                    </td>
                    <td>{formatPct(fold.strategy_return)}</td>
                    <td>{formatPct(fold.benchmark_return)}</td>
                    <td>{formatSharpe(fold.sharpe_ratio)}</td>
                    <td>{formatPct(fold.maximum_drawdown)}</td>
                    <td>{formatTrades(fold.trade_count)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}

      {walkForward.checks.length > 0 ? (
        <>
          <h4 className="research-subsection-title">{labels.checksTitle}</h4>
          <ul className="research-plain-list">
            {walkForward.checks.map((check) => (
              <li key={check.check_id}>
                {check.check_id}: {check.status}
                {check.observed_value != null
                  ? ` (observed ${check.observed_value}`
                  : " (observed n/a"}
                {check.configured_threshold != null
                  ? `, threshold ${check.configured_threshold})`
                  : ")"}
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {walkForward.limitations.length > 0 ? (
        <>
          <h4 className="research-subsection-title">{labels.limitationsTitle}</h4>
          <ul className="research-plain-list">
            {walkForward.limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}
