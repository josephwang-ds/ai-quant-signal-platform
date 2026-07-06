import type { Language } from "@/lib/i18n";
import type { SensitivityResponse, SensitivityResultRow } from "@/types/market";

const INTERP = {
  en: {
    concentrated:
      "Performance is concentrated in one parameter setting, so robustness should be tested carefully.",
    stable:
      "Performance appears more stable across parameter settings, which is a better robustness sign.",
    underperformMost:
      "Most parameter settings underperformed buy-and-hold, suggesting the MA crossover rule may not add value for this ticker and period.",
  },
  zh: {
    concentrated: "表现集中在某一组参数上，需要谨慎评估稳健性。",
    stable: "多组参数下表现较为稳定，这是更好的稳健性信号。",
    underperformMost:
      "多数参数组合跑输买入并持有，说明该标的在该区间内的均线交叉规则可能缺乏增量价值。",
  },
} as const;

/** 按 Sharpe 降序，其次 total_return 降序排序敏感性结果。 */
export function sortSensitivityResults(
  results: SensitivityResultRow[]
): SensitivityResultRow[] {
  return [...results].sort((a, b) => {
    const sharpeA = a.sharpe_ratio ?? Number.NEGATIVE_INFINITY;
    const sharpeB = b.sharpe_ratio ?? Number.NEGATIVE_INFINITY;
    if (sharpeA !== sharpeB) {
      return sharpeB - sharpeA;
    }
    const returnA = a.total_return ?? Number.NEGATIVE_INFINITY;
    const returnB = b.total_return ?? Number.NEGATIVE_INFINITY;
    return returnB - returnA;
  });
}

/** 基于规则生成参数敏感性分析解读。 */
export function generateSensitivityInterpretation(
  response: SensitivityResponse,
  lang: Language = "en"
): string[] {
  const sentences: string[] = [];
  const results = response.results;
  const text = INTERP[lang];

  if (results.length === 0) {
    return sentences;
  }

  const withSharpe = results.filter((row) => row.sharpe_ratio != null);
  if (withSharpe.length >= 2) {
    const sortedBySharpe = [...withSharpe].sort(
      (a, b) => (b.sharpe_ratio ?? 0) - (a.sharpe_ratio ?? 0)
    );
    const bestSharpe = sortedBySharpe[0].sharpe_ratio ?? 0;
    const secondSharpe = sortedBySharpe[1].sharpe_ratio ?? 0;
    if (bestSharpe - secondSharpe >= 0.5) {
      sentences.push(text.concentrated);
    }
  }

  const positiveReturns = results.filter((row) => (row.total_return ?? 0) > 0);
  const sharpes = results
    .map((row) => row.sharpe_ratio)
    .filter((value): value is number => value != null);

  if (positiveReturns.length >= 2 && sharpes.length >= 2) {
    const minSharpe = Math.min(...sharpes);
    const maxSharpe = Math.max(...sharpes);
    if (maxSharpe - minSharpe <= 0.3) {
      sentences.push(text.stable);
    }
  }

  const withBenchmark = results.filter(
    (row) => row.total_return != null && row.benchmark_return != null
  );
  if (withBenchmark.length > 0) {
    const underperformCount = withBenchmark.filter(
      (row) => (row.total_return ?? 0) < (row.benchmark_return ?? 0)
    ).length;
    if (underperformCount > withBenchmark.length / 2) {
      sentences.push(text.underperformMost);
    }
  }

  return sentences;
}
