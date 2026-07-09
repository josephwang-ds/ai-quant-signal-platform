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
  const shortId = run.id.slice(0, 8);
  const note = run.notes?.trim();
  if (note) {
    const clipped = note.length > 28 ? `${note.slice(0, 28)}…` : note;
    return `${clipped} (${shortId})`;
  }
  return `${run.ticker} · ${shortId}`;
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
  runs: BacktestRunSummary[]
): boolean {
  if (runs.length < 2) {
    return false;
  }

  const bestReturn = runsWithBestMetric(
    runs,
    (item) => item.metrics?.total_return ?? null,
    "max"
  );
  const bestSharpe = runsWithBestMetric(
    runs,
    (item) => item.metrics?.sharpe_ratio ?? null,
    "max"
  );
  const bestDrawdown = runsWithBestMetric(runs, getDrawdownMetric, "max");

  return (
    bestReturn.some((item) => item.id === run.id) ||
    bestSharpe.some((item) => item.id === run.id) ||
    bestDrawdown.some((item) => item.id === run.id)
  );
}

function runsWithBestMetric(
  runs: BacktestRunSummary[],
  pick: (run: BacktestRunSummary) => number | null,
  mode: "max" | "min"
): BacktestRunSummary[] {
  const scored = runs
    .map((run) => [run, pick(run)] as const)
    .filter((item): item is [BacktestRunSummary, number] => item[1] != null);
  if (scored.length === 0) {
    return [];
  }
  const target =
    mode === "max"
      ? Math.max(...scored.map((item) => item[1]))
      : Math.min(...scored.map((item) => item[1]));
  return scored.filter((item) => item[1] === target).map((item) => item[0]);
}
