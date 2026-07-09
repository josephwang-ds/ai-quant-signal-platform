import type { BacktestRunSummary } from "@/types/market";

export const MAX_COMPARE_RUNS = 4;

export type ExperimentCompareSummary = {
  bestTotalReturn: string | null;
  bestSharpe: string | null;
  lowestDrawdown: string | null;
};

function runLabel(run: BacktestRunSummary): string {
  const shortId = run.id.slice(0, 8);
  return `${run.ticker} · ${run.strategy} · ${shortId}`;
}

export function buildExperimentCompareLabel(run: BacktestRunSummary): string {
  return runLabel(run);
}

export function getDrawdownMetric(run: BacktestRunSummary): number | null {
  return (
    run.metrics?.strategy_max_drawdown ?? run.metrics?.max_drawdown ?? null
  );
}

export function buildExperimentCompareSummary(
  runs: BacktestRunSummary[]
): ExperimentCompareSummary {
  const summary: ExperimentCompareSummary = {
    bestTotalReturn: null,
    bestSharpe: null,
    lowestDrawdown: null,
  };

  const returnCandidates = runs
    .map((run) => [runLabel(run), run.metrics?.total_return] as const)
    .filter((item): item is [string, number] => item[1] != null);
  if (returnCandidates.length > 0) {
    summary.bestTotalReturn = returnCandidates.reduce((best, current) =>
      current[1] > best[1] ? current : best
    )[0];
  }

  const sharpeCandidates = runs
    .map((run) => [runLabel(run), run.metrics?.sharpe_ratio] as const)
    .filter((item): item is [string, number] => item[1] != null);
  if (sharpeCandidates.length > 0) {
    summary.bestSharpe = sharpeCandidates.reduce((best, current) =>
      current[1] > best[1] ? current : best
    )[0];
  }

  const drawdownCandidates = runs
    .map((run) => [runLabel(run), getDrawdownMetric(run)] as const)
    .filter((item): item is [string, number] => item[1] != null);
  if (drawdownCandidates.length > 0) {
    summary.lowestDrawdown = drawdownCandidates.reduce((best, current) =>
      current[1] > best[1] ? current : best
    )[0];
  }

  return summary;
}

export function isExperimentCompareHighlighted(
  run: BacktestRunSummary,
  summary: ExperimentCompareSummary
): boolean {
  const label = runLabel(run);
  return (
    label === summary.bestTotalReturn ||
    label === summary.bestSharpe ||
    label === summary.lowestDrawdown
  );
}
