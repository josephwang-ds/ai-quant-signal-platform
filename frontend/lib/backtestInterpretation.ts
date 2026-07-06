import type { Language } from "@/lib/i18n";
import type { BacktestResponse } from "@/types/market";

function formatPercentValue(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function formatPercentagePoints(diff: number): string {
  return `${(diff * 100).toFixed(2)}`;
}

const INTERP = {
  en: {
    outperformed: (pts: string) =>
      `The strategy outperformed buy-and-hold by ${pts} percentage points.`,
    underperformed: (pts: string) =>
      `The strategy underperformed buy-and-hold by ${pts} percentage points.`,
    inlineBenchmark: "The strategy performed roughly in line with buy-and-hold.",
    positiveReturn: "The strategy generated a positive return over the selected period.",
    negativeReturn: "The strategy lost money over the selected period.",
    flatReturn: "The strategy ended roughly flat over the selected period.",
    sharpeUnavailable:
      "Sharpe ratio is not available because return volatility is too low or data is insufficient.",
    sharpeStrong:
      "Sharpe ratio is above 1, suggesting relatively strong risk-adjusted performance.",
    sharpeModest:
      "Sharpe ratio is modest, suggesting acceptable but not strong risk-adjusted performance.",
    sharpeLow: "Sharpe ratio is low, suggesting weak risk-adjusted performance.",
    sharpeNegative:
      "Sharpe ratio is negative, meaning the strategy did not compensate well for risk.",
    ddMild: "Maximum drawdown was relatively mild.",
    ddMeaningful: "Maximum drawdown was meaningful and should be monitored.",
    ddSevere: "Maximum drawdown was severe, indicating high downside risk.",
    ddSmaller:
      "The strategy had a smaller maximum drawdown than buy-and-hold, suggesting better downside protection.",
    ddLarger:
      "The strategy had a larger maximum drawdown than buy-and-hold, suggesting weaker downside protection.",
    ddSimilar: "The strategy and benchmark had similar maximum drawdowns.",
    volLow: "Strategy volatility was relatively low.",
    volModerate: "Strategy volatility was moderate.",
    volHigh: "Strategy volatility was high.",
    tradesInfrequent:
      "The strategy traded infrequently, so transaction cost impact was limited.",
    tradesOccasional:
      "The strategy traded occasionally; transaction costs should be monitored.",
    tradesFrequent:
      "The strategy traded frequently, so transaction costs may materially affect performance.",
    txCost: (pct: string) =>
      `Total transaction cost impact was ${pct} over the backtest period.`,
    summaryInvestigate:
      "Overall, this backtest is worth further investigation, but it still needs testing across more tickers and time periods.",
    summaryUnderperform:
      "Overall, this strategy did not beat the benchmark in this test, but it may still be useful if it reduces drawdown in other periods.",
    summaryMixed:
      "Overall, this result is mixed and should be tested across more market regimes.",
  },
  zh: {
    outperformed: (pts: string) => `该策略跑赢买入并持有 ${pts} 个百分点。`,
    underperformed: (pts: string) => `该策略跑输买入并持有 ${pts} 个百分点。`,
    inlineBenchmark: "该策略表现与买入并持有大致相当。",
    positiveReturn: "该策略在所选区间内取得了正收益。",
    negativeReturn: "该策略在所选区间内出现亏损。",
    flatReturn: "该策略在所选区间内大致持平。",
    sharpeUnavailable: "Sharpe 比率不可用，可能因为收益波动过低或数据不足。",
    sharpeStrong: "Sharpe 比率高于 1，风险调整后表现相对较强。",
    sharpeModest: "Sharpe 比率处于中等水平，说明风险调整后表现尚可，但不算强。",
    sharpeLow: "Sharpe 比率偏低，风险调整后表现较弱。",
    sharpeNegative: "Sharpe 比率为负，说明策略未能有效补偿所承担的风险。",
    ddMild: "最大回撤相对温和。",
    ddMeaningful: "最大回撤较明显，需要重点关注下行风险。",
    ddSevere: "最大回撤严重，表明下行风险较高。",
    ddSmaller: "策略最大回撤小于买入并持有，下行保护可能更好。",
    ddLarger: "策略最大回撤大于买入并持有，下行保护可能较弱。",
    ddSimilar: "策略与基准的最大回撤大致相近。",
    volLow: "策略波动率相对较低。",
    volModerate: "策略波动率处于中等水平。",
    volHigh: "策略波动率较高。",
    tradesInfrequent: "该策略交易频率较低，因此交易成本影响有限。",
    tradesOccasional: "该策略交易频率一般，需关注交易成本影响。",
    tradesFrequent: "该策略交易频率较高，交易成本可能显著影响表现。",
    txCost: (pct: string) => `回测期间交易成本合计影响为 ${pct}。`,
    summaryInvestigate:
      "总体来看，该回测结果值得进一步研究，但仍需在更多标的与时间段上验证。",
    summaryUnderperform:
      "总体来看，该策略在本次测试中没有跑赢基准，但如果在其他区间能降低回撤，仍有研究价值。",
    summaryMixed: "总体来看，该结果好坏参半，应在更多市场环境中继续测试。",
  },
} as const;

// 根据回测指标生成初学者可读的解读句子
export function generateBacktestInterpretation(
  result: BacktestResponse,
  lang: Language = "en"
): string[] {
  const sentences: string[] = [];
  const metrics = result.metrics;
  const text = INTERP[lang];

  const totalReturn = metrics.total_return;
  const benchmarkReturn = metrics.benchmark_return;
  const sharpeRatio = metrics.sharpe_ratio;
  const strategyMaxDrawdown = metrics.strategy_max_drawdown ?? metrics.max_drawdown;
  const benchmarkMaxDrawdown = metrics.benchmark_max_drawdown;
  const volatility = metrics.volatility;
  const numberOfTrades = metrics.number_of_trades;
  const transactionCostTotal = metrics.transaction_cost_total;

  let benchmarkDiff: number | null = null;
  let outperformedBenchmark = false;
  let underperformedBenchmark = false;

  if (totalReturn != null && benchmarkReturn != null) {
    benchmarkDiff = totalReturn - benchmarkReturn;
    if (benchmarkDiff > 0) {
      outperformedBenchmark = true;
      sentences.push(text.outperformed(formatPercentagePoints(benchmarkDiff)));
    } else if (benchmarkDiff < 0) {
      underperformedBenchmark = true;
      sentences.push(
        text.underperformed(formatPercentagePoints(Math.abs(benchmarkDiff)))
      );
    } else {
      sentences.push(text.inlineBenchmark);
    }
  }

  if (totalReturn != null) {
    if (totalReturn > 0) {
      sentences.push(text.positiveReturn);
    } else if (totalReturn < 0) {
      sentences.push(text.negativeReturn);
    } else {
      sentences.push(text.flatReturn);
    }
  }

  if (sharpeRatio == null) {
    sentences.push(text.sharpeUnavailable);
  } else if (sharpeRatio >= 1) {
    sentences.push(text.sharpeStrong);
  } else if (sharpeRatio >= 0.5) {
    sentences.push(text.sharpeModest);
  } else if (sharpeRatio >= 0) {
    sentences.push(text.sharpeLow);
  } else {
    sentences.push(text.sharpeNegative);
  }

  if (strategyMaxDrawdown != null) {
    const absDrawdown = Math.abs(strategyMaxDrawdown);
    if (absDrawdown < 0.1) {
      sentences.push(text.ddMild);
    } else if (absDrawdown < 0.25) {
      sentences.push(text.ddMeaningful);
    } else {
      sentences.push(text.ddSevere);
    }
  }

  if (strategyMaxDrawdown != null && benchmarkMaxDrawdown != null) {
    const absStrategyDrawdown = Math.abs(strategyMaxDrawdown);
    const absBenchmarkDrawdown = Math.abs(benchmarkMaxDrawdown);
    if (absStrategyDrawdown < absBenchmarkDrawdown) {
      sentences.push(text.ddSmaller);
    } else if (absStrategyDrawdown > absBenchmarkDrawdown) {
      sentences.push(text.ddLarger);
    } else {
      sentences.push(text.ddSimilar);
    }
  }

  if (volatility != null) {
    if (volatility < 0.2) {
      sentences.push(text.volLow);
    } else if (volatility < 0.4) {
      sentences.push(text.volModerate);
    } else {
      sentences.push(text.volHigh);
    }
  }

  if (numberOfTrades != null) {
    if (numberOfTrades <= 3) {
      sentences.push(text.tradesInfrequent);
    } else if (numberOfTrades <= 20) {
      sentences.push(text.tradesOccasional);
    } else {
      sentences.push(text.tradesFrequent);
    }
  }

  if (transactionCostTotal != null) {
    sentences.push(text.txCost(formatPercentValue(transactionCostTotal)));
  }

  if (outperformedBenchmark && sharpeRatio != null && sharpeRatio >= 0.5) {
    sentences.push(text.summaryInvestigate);
  } else if (underperformedBenchmark) {
    sentences.push(text.summaryUnderperform);
  } else {
    sentences.push(text.summaryMixed);
  }

  return sentences;
}
