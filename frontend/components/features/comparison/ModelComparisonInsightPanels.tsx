"use client";

import type { ModelComparisonResponse, ModelComparisonResult } from "@/lib/api";
import {
  translateComparisonLabel,
  type TranslationKey,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function formatSharpe(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

function findRow(
  results: ModelComparisonResult[],
  label: string | null | undefined
): ModelComparisonResult | undefined {
  if (!label) return undefined;
  return results.find((row) => row.label === label);
}

export function buildComparisonConclusion(
  result: ModelComparisonResponse,
  language: "en" | "zh"
): string {
  const { summary, results } = result;
  const bestSharpe = findRow(results, summary.best_sharpe);
  const bestReturn = findRow(results, summary.best_total_return);
  const lowestDd = findRow(results, summary.lowest_drawdown);
  const fewest = findRow(results, summary.fewest_trades);

  const name = (row?: ModelComparisonResult) =>
    row ? translateComparisonLabel(language, row.label) : "—";

  const sharpeVal = formatSharpe(bestSharpe?.metrics.sharpe_ratio);
  const retVal = formatPct(bestReturn?.metrics.total_return);
  const ddVal = formatPct(
    lowestDd?.metrics.strategy_max_drawdown ?? lowestDd?.metrics.max_drawdown
  );
  const trades = fewest?.metrics.number_of_trades;
  const cost = formatPct(bestSharpe?.metrics.transaction_cost_total ?? null);

  if (language === "zh") {
    return (
      `样本外最佳 Sharpe=${sharpeVal}（${name(bestSharpe)}）；` +
      `最高收益=${retVal}（${name(bestReturn)}）；` +
      `最低回撤=${ddVal}（${name(lowestDd)}）。` +
      `换手方面，最少交易约为 ${trades ?? "—"} 次；` +
      `最佳 Sharpe 行累计交易成本约 ${cost}。` +
      `上述排名仅对该样本外窗口成立，未必在其它区间也最好——请结合 walk-forward 逐折稳定性查看。`
    );
  }

  return (
    `Best OOS Sharpe=${sharpeVal} (${name(bestSharpe)}); ` +
    `highest return=${retVal} (${name(bestReturn)}); ` +
    `lowest drawdown=${ddVal} (${name(lowestDd)}). ` +
    `Turnover: fewest trades ≈ ${trades ?? "—"}; ` +
    `transaction cost on the best-Sharpe row ≈ ${cost}. ` +
    `These rankings hold for this OOS window only — they may not transfer; ` +
    `check walk-forward fold stability.`
  );
}

const FAMILY_KEYS: TranslationKey[] = [
  "modelComparisonMethodFamilyLinear",
  "modelComparisonMethodFamilyTrees",
  "modelComparisonMethodFamilySvm",
  "modelComparisonMethodFamilyRegression",
  "modelComparisonMethodFamilyTimeseries",
  "modelComparisonMethodFamilyDl",
];

type Props = {
  result: ModelComparisonResponse;
  onExplain?: () => void;
  explaining?: boolean;
  copilotExplanation?: string | null;
};

export default function ModelComparisonInsightPanels({
  result,
  onExplain,
  explaining,
  copilotExplanation,
}: Props) {
  const { language, tr } = useWorkspaceLanguage();
  const conclusion = buildComparisonConclusion(result, language);

  return (
    <div className="model-comparison-insight-panels">
      <details className="model-comparison-methodology" open={false}>
        <summary>{tr("modelComparisonMethodologyTitle")}</summary>
        <p className="model-comparison-methodology__lead">
          {tr("modelComparisonMethodologyLead")}
        </p>
        <div
          className="model-comparison-methodology__diagram"
          aria-hidden="true"
        >
          <span>{tr("modelComparisonMethodStepTrain")}</span>
          <span aria-hidden="true">→</span>
          <span>{tr("modelComparisonMethodStepEmbargo")}</span>
          <span aria-hidden="true">→</span>
          <span>{tr("modelComparisonMethodStepOos")}</span>
          <span aria-hidden="true">→</span>
          <span>{tr("modelComparisonMethodStepBacktest")}</span>
        </div>
        <ul className="model-comparison-methodology__families">
          {FAMILY_KEYS.map((key) => (
            <li key={key}>{tr(key)}</li>
          ))}
        </ul>
      </details>

      <section
        className="model-comparison-conclusion"
        aria-label={tr("modelComparisonConclusionTitle")}
      >
        <h3 className="model-comparison-conclusion__title">
          {tr("modelComparisonConclusionTitle")}
        </h3>
        <p className="model-comparison-conclusion__body">{conclusion}</p>
        {onExplain ? (
          <div className="model-comparison-conclusion__actions">
            <button
              type="button"
              className="model-comparison-view-toggle__btn"
              onClick={onExplain}
              disabled={explaining}
            >
              {explaining
                ? tr("modelComparisonExplainRunning")
                : tr("modelComparisonExplainWithCopilot")}
            </button>
          </div>
        ) : null}
        {copilotExplanation ? (
          <p className="model-comparison-conclusion__copilot">
            <strong>{tr("modelComparisonExplainLabel")}:</strong>{" "}
            {copilotExplanation}
          </p>
        ) : null}
      </section>
    </div>
  );
}
