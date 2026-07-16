import type { ExecutionMetrics } from "@/types/researchExecution";
import type {
  ResearchValidationResult,
  ValidationStageStatus,
} from "@/types/researchValidation";
import type { Language } from "@/lib/i18n";

export type ResearchValidationLabels = {
  title: string;
  summary: string;
  status: string;
  evidenceComplete: string;
  yes: string;
  no: string;
  completed: string;
  incomplete: string;
  failed: string;
  unavailable: string;
  source: string;
  generated: string;
  rules: string;
  warnings: string;
  blockers: string;
  evidence: string;
  oosTitle: string;
  splitDate: string;
  inSampleRatio: string;
  minimumOos: string;
  boundary: string;
  inSample: string;
  outOfSample: string;
  benchmark: string;
  observations: string;
  metric: string;
  totalReturn: string;
  cagr: string;
  sharpe: string;
  maxDrawdown: string;
  volatility: string;
  trades: string;
  totalCosts: string;
  parameterTitle: string;
  validCombinations: string;
  profitableCombinations: string;
  positiveSharpe: string;
  medianSharpe: string;
  sharpeRange: string;
  medianDrawdown: string;
  canonicalPercentile: string;
  shortWindow: string;
  longWindow: string;
  canonical: string;
  costTitle: string;
  transactionCost: string;
  returnDegradation: string;
  sharpeDegradation: string;
  mathematicallyValid: string;
  canonicalCost: string;
  dataQualityTitle: string;
  provider: string;
  dateRange: string;
  cache: string;
  cacheHit: string;
  cacheMiss: string;
  fatalIssues: string;
  checks: string;
  check: string;
  severity: string;
  details: string;
  notAvailable: string;
};

type Props = {
  validation: ResearchValidationResult;
  labels: ResearchValidationLabels;
  language: Language;
};

function formatNumber(value: number | null | undefined): string {
  return value == null || Number.isNaN(value) ? "n/a" : value.toFixed(2);
}

function formatInteger(value: number | null | undefined): string {
  return value == null || Number.isNaN(value) ? "n/a" : String(Math.round(value));
}

function formatPercent(value: number | null | undefined): string {
  return value == null || Number.isNaN(value)
    ? "n/a"
    : `${(value * 100).toFixed(2)}%`;
}

function statusLabel(
  status: ValidationStageStatus,
  labels: ResearchValidationLabels
): string {
  return labels[status];
}

function statusTone(status: ValidationStageStatus): string {
  if (status === "completed") return "success";
  if (status === "failed") return "danger";
  if (status === "incomplete") return "warning";
  return "neutral";
}

function localizeBackendText(value: string, language: Language): string {
  if (language !== "zh") return value;
  const known: Record<string, string> = {
    "Yahoo Finance / yfinance is suitable for research and portfolio demos only — not an exchange-grade production feed.":
      "Yahoo Finance / yfinance 仅适合研究与作品集演示，不属于交易所级生产数据源。",
    "Provider timeout is enforced via yfinance download(timeout=…).":
      "数据下载已设置超时保护。",
    "Yahoo prices use yfinance auto_adjust (auto_adjust).":
      "Yahoo 行情使用 yfinance 自动复权价格（auto_adjust）。",
    "The strategy is run once on full history, then valid return rows are sliced at split_date. The first OOS row therefore preserves its full-run position, turnover, and transaction cost against the prior in-sample row.":
      "策略先在完整历史区间运行，再按切分日期划分有效收益；首个样本外观测会保留与上一样本内观测连续的仓位、换手和交易成本。",
  };
  return known[value] ?? value;
}

function WarningList({
  title,
  items,
  language,
  tone = "warning",
}: {
  title: string;
  items: string[];
  language: Language;
  tone?: "warning" | "danger";
}) {
  if (items.length === 0) return null;
  return (
    <div className={`validation-evidence__messages validation-evidence__messages--${tone}`}>
      <strong>{title}</strong>
      <ul>
        {items.map((item, index) => (
          <li key={`${item}-${index}`}>{localizeBackendText(item, language)}</li>
        ))}
      </ul>
    </div>
  );
}

const METRIC_ROWS: Array<{
  key: keyof ExecutionMetrics;
  label: keyof ResearchValidationLabels;
  format: (value: number | null | undefined) => string;
}> = [
  { key: "total_return", label: "totalReturn", format: formatPercent },
  { key: "cagr", label: "cagr", format: formatPercent },
  { key: "sharpe_ratio", label: "sharpe", format: formatNumber },
  { key: "maximum_drawdown", label: "maxDrawdown", format: formatPercent },
  { key: "annualized_volatility", label: "volatility", format: formatPercent },
  { key: "trade_count", label: "trades", format: formatInteger },
  {
    key: "total_transaction_costs",
    label: "totalCosts",
    format: formatPercent,
  },
];

function OosEvidence({
  validation,
  labels,
  language,
}: Props) {
  const oos = validation.oos;
  const metricSets = [
    oos.in_sample_metrics,
    oos.out_of_sample_metrics,
    oos.oos_benchmark_metrics,
  ];
  return (
    <section className="validation-detail" aria-labelledby="validation-oos-title">
      <div className="validation-detail__heading">
        <h3 id="validation-oos-title">{labels.oosTitle}</h3>
        <span className={`badge badge--${statusTone(oos.status)}`}>
          {statusLabel(oos.status, labels)}
        </span>
      </div>
      <dl className="validation-evidence__facts">
        <div><dt>{labels.splitDate}</dt><dd>{oos.split_date ?? labels.notAvailable}</dd></div>
        <div><dt>{labels.inSampleRatio}</dt><dd>{formatPercent(oos.in_sample_ratio)}</dd></div>
        <div><dt>{labels.minimumOos}</dt><dd>{formatInteger(oos.minimum_oos_observations)}</dd></div>
        <div><dt>{labels.boundary}</dt><dd>{oos.boundary_convention ? localizeBackendText(oos.boundary_convention, language) : labels.notAvailable}</dd></div>
        <div><dt>{labels.inSample} {labels.observations}</dt><dd>{formatInteger(oos.in_sample_observation_count)}</dd></div>
        <div><dt>{labels.outOfSample} {labels.observations}</dt><dd>{formatInteger(oos.out_of_sample_observation_count)}</dd></div>
      </dl>
      <div className="validation-table-wrap">
        <table className="data-table validation-table">
          <caption>{labels.oosTitle}</caption>
          <thead><tr><th>{labels.metric}</th><th>{labels.inSample}</th><th>{labels.outOfSample}</th><th>{labels.benchmark}</th></tr></thead>
          <tbody>
            {METRIC_ROWS.map((row) => (
              <tr key={row.key}>
                <th scope="row">{labels[row.label]}</th>
                {metricSets.map((metrics, index) => (
                  <td key={index} className="num">{row.format(metrics?.[row.key] as number | null | undefined)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <WarningList title={labels.warnings} items={oos.warnings} language={language} />
    </section>
  );
}

function ParameterEvidence({ validation, labels, language }: Props) {
  const sensitivity = validation.parameter_sensitivity;
  return (
    <section className="validation-detail" aria-labelledby="validation-parameter-title">
      <div className="validation-detail__heading">
        <h3 id="validation-parameter-title">{labels.parameterTitle}</h3>
        <span className={`badge badge--${statusTone(sensitivity.status)}`}>{statusLabel(sensitivity.status, labels)}</span>
      </div>
      <dl className="validation-evidence__facts">
        <div><dt>{labels.validCombinations}</dt><dd>{formatInteger(sensitivity.valid_combination_count)}</dd></div>
        <div><dt>{labels.profitableCombinations}</dt><dd>{formatInteger(sensitivity.profitable_combination_count)}</dd></div>
        <div><dt>{labels.positiveSharpe}</dt><dd>{formatInteger(sensitivity.positive_sharpe_count)}</dd></div>
        <div><dt>{labels.medianSharpe}</dt><dd>{formatNumber(sensitivity.median_sharpe)}</dd></div>
        <div><dt>{labels.sharpeRange}</dt><dd>{sensitivity.sharpe_range.map(formatNumber).join(" → ")}</dd></div>
        <div><dt>{labels.medianDrawdown}</dt><dd>{formatPercent(sensitivity.median_max_drawdown)}</dd></div>
        <div><dt>{labels.canonicalPercentile}</dt><dd>{formatPercent(sensitivity.canonical_percentile_by_sharpe)}</dd></div>
      </dl>
      <div className="validation-table-wrap">
        <table className="data-table validation-table">
          <caption>{labels.parameterTitle}</caption>
          <thead><tr><th>{labels.shortWindow}</th><th>{labels.longWindow}</th><th>{labels.totalReturn}</th><th>{labels.cagr}</th><th>{labels.sharpe}</th><th>{labels.maxDrawdown}</th><th>{labels.volatility}</th><th>{labels.trades}</th></tr></thead>
          <tbody>
            {sensitivity.results.map((result, index) => (
              <tr className={result.is_canonical ? "is-canonical" : undefined} key={`${result.short_window}-${result.long_window}-${index}`}>
                <td>{formatInteger(result.short_window)} {result.is_canonical ? <span className="badge badge--info">{labels.canonical}</span> : null}</td>
                <td className="num">{formatInteger(result.long_window)}</td>
                <td className="num">{formatPercent(result.total_return)}</td>
                <td className="num">{formatPercent(result.cagr)}</td>
                <td className="num">{formatNumber(result.sharpe_ratio)}</td>
                <td className="num">{formatPercent(result.maximum_drawdown)}</td>
                <td className="num">{formatPercent(result.annualized_volatility)}</td>
                <td className="num">{formatInteger(result.trade_count)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <WarningList title={labels.warnings} items={sensitivity.warnings} language={language} />
    </section>
  );
}

function CostEvidence({ validation, labels, language }: Props) {
  const costs = validation.transaction_cost_sensitivity;
  return (
    <section className="validation-detail" aria-labelledby="validation-cost-title">
      <div className="validation-detail__heading">
        <h3 id="validation-cost-title">{labels.costTitle}</h3>
        <span className={`badge badge--${statusTone(costs.status)}`}>{statusLabel(costs.status, labels)}</span>
      </div>
      <p className="validation-detail__note">{labels.canonicalCost}: {formatPercent(costs.canonical_cost)}</p>
      <div className="validation-table-wrap">
        <table className="data-table validation-table">
          <caption>{labels.costTitle}</caption>
          <thead><tr><th>{labels.transactionCost}</th><th>{labels.totalReturn}</th><th>{labels.cagr}</th><th>{labels.sharpe}</th><th>{labels.maxDrawdown}</th><th>{labels.trades}</th><th>{labels.totalCosts}</th><th>{labels.returnDegradation}</th><th>{labels.sharpeDegradation}</th><th>{labels.mathematicallyValid}</th></tr></thead>
          <tbody>
            {costs.results.map((result, index) => (
              <tr key={`${result.transaction_cost}-${index}`}>
                <td className="num">{formatPercent(result.transaction_cost)}</td>
                <td className="num">{formatPercent(result.total_return)}</td>
                <td className="num">{formatPercent(result.cagr)}</td>
                <td className="num">{formatNumber(result.sharpe_ratio)}</td>
                <td className="num">{formatPercent(result.maximum_drawdown)}</td>
                <td className="num">{formatInteger(result.trade_count)}</td>
                <td className="num">{formatPercent(result.total_transaction_costs)}</td>
                <td className="num">{formatPercent(result.return_degradation_from_zero)}</td>
                <td className="num">{formatNumber(result.sharpe_degradation_from_zero)}</td>
                <td>{result.mathematically_valid ? labels.yes : labels.no}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <WarningList title={labels.warnings} items={costs.warnings} language={language} />
    </section>
  );
}

function DataQualityEvidence({ validation, labels, language }: Props) {
  const quality = validation.data_quality;
  const provenance = validation.provenance;
  return (
    <section className="validation-detail" aria-labelledby="validation-quality-title">
      <div className="validation-detail__heading">
        <h3 id="validation-quality-title">{labels.dataQualityTitle}</h3>
        <span className={`badge badge--${statusTone(quality.status)}`}>{statusLabel(quality.status, labels)}</span>
      </div>
      <dl className="validation-evidence__facts">
        <div><dt>{labels.provider}</dt><dd>{provenance.source || provenance.provider}</dd></div>
        <div><dt>{labels.dateRange}</dt><dd>{provenance.actual_start} → {provenance.actual_end}</dd></div>
        <div><dt>{labels.generated}</dt><dd>{validation.generated_at}</dd></div>
        <div><dt>{labels.cache}</dt><dd>{provenance.cache_hit ? labels.cacheHit : labels.cacheMiss}</dd></div>
        <div><dt>{labels.fatalIssues}</dt><dd>{quality.fatal_issues.length}</dd></div>
        <div><dt>{labels.warnings}</dt><dd>{quality.warnings.length}</dd></div>
      </dl>
      <WarningList title={labels.fatalIssues} items={quality.fatal_issues} language={language} tone="danger" />
      <WarningList title={labels.warnings} items={quality.warnings} language={language} />
    </section>
  );
}

export default function ResearchValidationPanel({ validation, labels, language }: Props) {
  return (
    <section className="research-validation" aria-labelledby="research-validation-title">
      <header className="research-validation__header">
        <div>
          <h2 id="research-validation-title">{labels.title}</h2>
          <p>{labels.summary}</p>
        </div>
        <span className={`badge badge--${statusTone(validation.validation_status)}`}>
          {statusLabel(validation.validation_status, labels)}
        </span>
      </header>
      <dl className="validation-evidence__facts validation-evidence__facts--summary">
        <div><dt>{labels.status}</dt><dd>{statusLabel(validation.validation_status, labels)}</dd></div>
        <div><dt>{labels.evidenceComplete}</dt><dd>{validation.evidence_complete ? labels.yes : labels.no}</dd></div>
        <div><dt>{labels.source}</dt><dd>{validation.provenance.source || validation.provenance.provider}</dd></div>
        <div><dt>{labels.generated}</dt><dd>{validation.generated_at}</dd></div>
      </dl>
      <WarningList title={labels.warnings} items={validation.warnings} language={language} />
      <OosEvidence validation={validation} labels={labels} language={language} />
      <ParameterEvidence validation={validation} labels={labels} language={language} />
      <CostEvidence validation={validation} labels={labels} language={language} />
      <DataQualityEvidence validation={validation} labels={labels} language={language} />
    </section>
  );
}
