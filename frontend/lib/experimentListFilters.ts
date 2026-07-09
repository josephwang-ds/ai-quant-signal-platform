import type { BacktestRunSummary } from "@/types/market";
import { getDrawdownMetric } from "@/lib/experimentCompare";

export type ExperimentSortKey =
  | "created_at"
  | "total_return"
  | "sharpe_ratio"
  | "drawdown";

export type ExperimentSortDirection = "asc" | "desc";

export type ExperimentListFilters = {
  ticker: string;
  strategy: string;
  sortKey: ExperimentSortKey;
  sortDirection: ExperimentSortDirection;
};

export const DEFAULT_EXPERIMENT_LIST_FILTERS: ExperimentListFilters = {
  ticker: "all",
  strategy: "all",
  sortKey: "created_at",
  sortDirection: "desc",
};

function metricValue(
  run: BacktestRunSummary,
  key: ExperimentSortKey
): number | null {
  switch (key) {
    case "created_at":
      return new Date(run.created_at).getTime();
    case "total_return":
      return run.metrics?.total_return ?? null;
    case "sharpe_ratio":
      return run.metrics?.sharpe_ratio ?? null;
    case "drawdown":
      return getDrawdownMetric(run);
  }
}

function compareNullableNumbers(
  left: number | null,
  right: number | null,
  direction: ExperimentSortDirection
): number {
  if (left == null && right == null) {
    return 0;
  }
  if (left == null) {
    return 1;
  }
  if (right == null) {
    return -1;
  }
  const diff = left - right;
  return direction === "asc" ? diff : -diff;
}

export function getUniqueExperimentTickers(runs: BacktestRunSummary[]): string[] {
  return [...new Set(runs.map((run) => run.ticker))].sort();
}

export function getUniqueExperimentStrategies(
  runs: BacktestRunSummary[]
): string[] {
  return [...new Set(runs.map((run) => run.strategy))].sort();
}

export function sanitizeExperimentListFilters(
  filters: ExperimentListFilters,
  runs: BacktestRunSummary[]
): ExperimentListFilters {
  const tickers = getUniqueExperimentTickers(runs);
  const strategies = getUniqueExperimentStrategies(runs);
  return {
    ...filters,
    ticker:
      filters.ticker !== "all" && !tickers.includes(filters.ticker)
        ? "all"
        : filters.ticker,
    strategy:
      filters.strategy !== "all" && !strategies.includes(filters.strategy)
        ? "all"
        : filters.strategy,
  };
}

export function filterAndSortExperimentRuns(
  runs: BacktestRunSummary[],
  filters: ExperimentListFilters
): BacktestRunSummary[] {
  const filtered = runs.filter((run) => {
    if (filters.ticker !== "all" && run.ticker !== filters.ticker) {
      return false;
    }
    if (filters.strategy !== "all" && run.strategy !== filters.strategy) {
      return false;
    }
    return true;
  });

  return [...filtered].sort((left, right) => {
    const primary = compareNullableNumbers(
      metricValue(left, filters.sortKey),
      metricValue(right, filters.sortKey),
      filters.sortDirection
    );
    if (primary !== 0) {
      return primary;
    }
    return compareNullableNumbers(
      metricValue(left, "created_at"),
      metricValue(right, "created_at"),
      "desc"
    );
  });
}
