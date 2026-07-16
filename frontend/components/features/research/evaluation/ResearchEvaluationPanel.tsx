import type {
  EvaluationStatus,
  ResearchEvaluationResult,
} from "@/types/researchEvaluation";
import type { Language } from "@/lib/i18n";

/**
 * Enterprise governance dashboard for PR-010 evaluation evidence.
 *
 * This panel renders only backend-derived summarization of PR-009
 * validation evidence. It never renders a score, confidence, star rating,
 * or buy/sell recommendation — evaluation answers "do we have enough
 * trustworthy evidence to continue research?", not "should we buy?".
 */

export type ResearchEvaluationLabels = {
  title: string;
  summary: string;
  status: string;
  completed: string;
  incomplete: string;
  blocked: string;
  source: string;
  generated: string;
  coverageTitle: string;
  implementedStages: string;
  completedStagesCount: string;
  coveragePercentage: string;
  coverageDisclaimer: string;
  evidenceSummaryTitle: string;
  stageColumn: string;
  statusColumn: string;
  summaryColumn: string;
  completedEvidenceTitle: string;
  incompleteEvidenceTitle: string;
  outstandingEvidenceTitle: string;
  limitationsTitle: string;
  blockersTitle: string;
  none: string;
  notAvailable: string;
};

type Props = {
  evaluation: ResearchEvaluationResult;
  labels: ResearchEvaluationLabels;
  language: Language;
};

function localizeEvaluationText(value: string, language: Language): string {
  if (language !== "zh") return value;
  const exact: Record<string, string> = {
    "Historical backtest": "历史回测",
    "Benchmark comparison": "基准对比",
    "Out-of-sample validation": "样本外验证",
    "Parameter sensitivity": "参数敏感性",
    "Transaction-cost sensitivity": "交易成本敏感性",
    "Data quality": "数据质量",
    "Stress testing": "压力测试",
    "Regime analysis": "市场状态分析",
    "Walk-forward validation": "滚动前向验证",
    "Monte Carlo simulation": "蒙特卡洛模拟",
    "Paper trading": "模拟试盘",
    "Full-history deterministic MA-crossover evidence was calculated.": "已完成全历史区间的确定性均线交叉回测。",
    "The strategy was compared with same-asset buy-and-hold.": "策略已与同一标的的买入并持有基准完成对比。",
    "Chronological OOS evidence completed with fixed parameters.": "已使用固定参数完成按时间顺序切分的样本外验证。",
    "Data-quality review found 0 fatal issues and 3 non-fatal limitations.": "数据质量检查未发现致命问题，记录了 3 项非致命限制。",
    "Evaluation is based on historical evidence only; it performs no new calculations.": "评估仅基于历史证据，不执行新的计算。",
    "Independent benchmark comparison is unavailable; benchmark evidence uses same-asset buy-and-hold only.": "当前基准证据仅使用同一标的买入并持有，尚无独立基准对比。",
    "Stress testing is not implemented.": "尚未完成压力测试。",
    "Regime analysis is not implemented.": "尚未完成市场状态分析。",
    "Walk-forward validation is not implemented.": "尚未完成滚动前向验证。",
    "Monte Carlo simulation is not implemented.": "尚未完成蒙特卡洛模拟。",
    "Research has not been published.": "研究尚未发布。",
    "Paper trading is unavailable.": "尚未进入模拟试盘。",
  };
  if (exact[value]) return exact[value];
  const parameterMatch = value.match(/^(\d+) of (\d+) deterministic parameter combinations produced metrics; no parameter was selected\.$/);
  if (parameterMatch) return `${parameterMatch[2]} 组确定性参数组合中有 ${parameterMatch[1]} 组生成了指标，系统未自动选择最优参数。`;
  const costMatch = value.match(/^(\d+) of (\d+) deterministic transaction-cost levels produced metrics\.$/);
  if (costMatch) return `${costMatch[2]} 档确定性交易成本中有 ${costMatch[1]} 档生成了指标。`;
  return value;
}

function statusTone(status: string): string {
  if (status === "completed") return "success";
  if (status === "blocked" || status === "failed") return "danger";
  if (status === "incomplete") return "warning";
  return "neutral";
}

function statusLabel(
  status: EvaluationStatus | string,
  labels: ResearchEvaluationLabels
): string {
  if (status === "completed") return labels.completed;
  if (status === "incomplete") return labels.incomplete;
  if (status === "blocked") return labels.blocked;
  return status;
}

function EvidenceList({
  title,
  items,
  emptyLabel,
  tone,
  language,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
  tone?: "warning" | "danger";
  language: Language;
}) {
  return (
    <section className="evaluation-list-card" aria-label={title}>
      <h3>{title}</h3>
      {items.length === 0 ? (
        <p className="section-meta">{emptyLabel}</p>
      ) : (
        <ul
          className={
            tone
              ? `validation-evidence__list evaluation-list--${tone}`
              : "validation-evidence__list"
          }
        >
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{localizeEvaluationText(item, language)}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function ResearchEvaluationPanel({
  evaluation,
  labels,
  language,
}: Props) {
  const coverage = evaluation.evidence_coverage;
  const provenance = evaluation.provenance;

  return (
    <section
      className="research-evaluation"
      aria-labelledby="research-evaluation-title"
    >
      <header className="research-evaluation__header">
        <div>
          <h2 id="research-evaluation-title">{labels.title}</h2>
          <p>{labels.summary}</p>
        </div>
        <span
          className={`badge badge--${statusTone(evaluation.evaluation_status)}`}
        >
          {statusLabel(evaluation.evaluation_status, labels)}
        </span>
      </header>

      <dl className="validation-evidence__facts validation-evidence__facts--summary">
        <div>
          <dt>{labels.status}</dt>
          <dd>{statusLabel(evaluation.evaluation_status, labels)}</dd>
        </div>
        <div>
          <dt>{labels.source}</dt>
          <dd>
            {(provenance.market_data_provenance?.["source"] as string) ??
              (provenance.market_data_provenance?.["provider"] as string) ??
              labels.notAvailable}
          </dd>
        </div>
        <div>
          <dt>{labels.generated}</dt>
          <dd>{evaluation.generated_at}</dd>
        </div>
      </dl>

      <section
        className="evaluation-coverage-card"
        aria-labelledby="research-evaluation-coverage-title"
      >
        <h3 id="research-evaluation-coverage-title">{labels.coverageTitle}</h3>
        <dl className="validation-evidence__facts">
          <div>
            <dt>{labels.implementedStages}</dt>
            <dd>{coverage.implemented_stage_count}</dd>
          </div>
          <div>
            <dt>{labels.completedStagesCount}</dt>
            <dd>{coverage.completed_stage_count}</dd>
          </div>
          <div>
            <dt>{labels.coveragePercentage}</dt>
            <dd>{coverage.coverage_percentage}%</dd>
          </div>
        </dl>
        <div
          className="evaluation-coverage-bar"
          role="img"
          aria-label={`${coverage.coverage_percentage}%`}
        >
          <div
            className="evaluation-coverage-bar__fill"
            style={{ width: `${Math.min(100, Math.max(0, coverage.coverage_percentage))}%` }}
          />
        </div>
        <p className="validation-detail__note">{labels.coverageDisclaimer}</p>
      </section>

      <section
        className="evaluation-evidence-summary"
        aria-labelledby="research-evaluation-summary-title"
      >
        <h3 id="research-evaluation-summary-title">
          {labels.evidenceSummaryTitle}
        </h3>
        <div className="validation-table-wrap">
          <table className="data-table validation-table">
            <caption>{labels.evidenceSummaryTitle}</caption>
            <thead>
              <tr>
                <th>{labels.stageColumn}</th>
                <th>{labels.statusColumn}</th>
                <th>{labels.summaryColumn}</th>
              </tr>
            </thead>
            <tbody>
              {evaluation.evidence_summary.map((item) => (
                <tr key={item.stage}>
                  <th scope="row">{localizeEvaluationText(item.label, language)}</th>
                  <td>
                    <span className={`badge badge--${statusTone(item.status)}`}>
                      {statusLabel(item.status, labels)}
                    </span>
                  </td>
                  <td>{localizeEvaluationText(item.summary, language)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="evaluation-list-grid">
        <EvidenceList
          title={labels.completedEvidenceTitle}
          items={evaluation.completed_stages}
          emptyLabel={labels.none}
          language={language}
        />
        <EvidenceList
          title={labels.incompleteEvidenceTitle}
          items={evaluation.incomplete_stages}
          emptyLabel={labels.none}
          tone="warning"
          language={language}
        />
        <EvidenceList
          title={labels.outstandingEvidenceTitle}
          items={evaluation.outstanding_evidence}
          emptyLabel={labels.none}
          language={language}
        />
        <EvidenceList
          title={labels.limitationsTitle}
          items={evaluation.limitations}
          emptyLabel={labels.none}
          language={language}
        />
      </div>

      <EvidenceList
        title={labels.blockersTitle}
        items={evaluation.blockers}
        emptyLabel={labels.none}
        tone="danger"
        language={language}
      />
    </section>
  );
}
