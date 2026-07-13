import type { Language } from "@/lib/i18n";
import type { BacktestResponse } from "@/types/market";

export type BacktestRiskLevel =
  | "Green"
  | "Light Yellow"
  | "Yellow"
  | "Orange"
  | "Red";

export type PaperTradingEligibility = "eligible" | "watch" | "not_eligible";

/** 供 Decision Room / LLM Explainer 预留的回测解释载荷 */
export type BacktestExplanationPayload = {
  strategy: string;
  symbol: string;
  totalReturn: number | null;
  benchmarkReturn: number | null;
  excessReturn: number | null;
  maxDrawdown: number | null;
  sharpeRatio: number | null;
  tradeCount: number | null;
  costPaid: number | null;
  backtestRiskLevel: BacktestRiskLevel;
  paperTradingEligibility: PaperTradingEligibility;
  reviewFindings: string[];
};

function formatPct(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function resolveMaxDrawdown(metrics: BacktestResponse["metrics"]): number | null {
  return metrics.strategy_max_drawdown ?? metrics.max_drawdown;
}

/** 基于最大回撤的五档回测风险等级（前端规则） */
export function calculateBacktestRiskLevel(maxDrawdown: number | null): BacktestRiskLevel {
  if (maxDrawdown == null) {
    return "Green";
  }
  if (maxDrawdown >= -0.03) {
    return "Green";
  }
  if (maxDrawdown >= -0.06) {
    return "Light Yellow";
  }
  if (maxDrawdown >= -0.1) {
    return "Yellow";
  }
  if (maxDrawdown >= -0.15) {
    return "Orange";
  }
  return "Red";
}

/** 模拟试盘准入建议 */
export function calculatePaperTradingEligibility(
  riskLevel: BacktestRiskLevel
): PaperTradingEligibility {
  if (riskLevel === "Green" || riskLevel === "Light Yellow") {
    return "eligible";
  }
  if (riskLevel === "Yellow") {
    return "watch";
  }
  return "not_eligible";
}

function sharpeAssessment(sharpe: number | null, lang: Language): string {
  if (sharpe == null) {
    return lang === "zh" ? "夏普比率不可用。" : "Sharpe ratio is unavailable.";
  }
  if (sharpe >= 1) {
    return lang === "zh"
      ? "夏普比率表明风险调整后收益较强。"
      : "Sharpe ratio suggests strong risk-adjusted return.";
  }
  if (sharpe >= 0.5) {
    return lang === "zh"
      ? "夏普比率表明风险调整后收益尚可。"
      : "Sharpe ratio suggests acceptable risk-adjusted return.";
  }
  return lang === "zh"
    ? "夏普比率表明风险调整后收益偏弱。"
    : "Sharpe ratio suggests weak risk-adjusted return.";
}

function costDragAssessment(
  costTotal: number | null,
  totalReturn: number | null,
  lang: Language
): string {
  if (costTotal == null) {
    return lang === "zh"
      ? "交易成本数据不可用。"
      : "Transaction cost data is unavailable.";
  }
  const pct = formatPct(Math.abs(costTotal));
  let pressure: string;
  if (totalReturn == null || Math.abs(totalReturn) < 1e-9) {
    pressure = lang === "zh" ? "中等" : "moderate";
  } else {
    const ratio = Math.abs(costTotal / totalReturn);
    if (ratio < 0.1) {
      pressure = lang === "zh" ? "较低" : "low";
    } else if (ratio < 0.35) {
      pressure = lang === "zh" ? "中等" : "moderate";
    } else {
      pressure = lang === "zh" ? "较高" : "high";
    }
  }
  return lang === "zh"
    ? `交易成本拖累为 ${pct}，成本压力${pressure === "较低" ? "较低" : pressure === "中等" ? "中等" : "较高"}。`
    : `Transaction cost drag was ${pct}, indicating ${pressure} cost pressure.`;
}

function turnoverAssessment(tradeCount: number | null, lang: Language): string {
  if (tradeCount == null) {
    return lang === "zh" ? "交易次数数据不可用。" : "Trade count is unavailable.";
  }
  let level: string;
  if (tradeCount <= 5) {
    level = lang === "zh" ? "较低" : "low";
  } else if (tradeCount <= 20) {
    level = lang === "zh" ? "中等" : "moderate";
  } else {
    level = lang === "zh" ? "偏高" : "excessive";
  }
  return lang === "zh"
    ? `交易次数为 ${tradeCount} 次，换手程度${level === "较低" ? "较低" : level === "中等" ? "中等" : "偏高"}。`
    : `Trade count (${tradeCount}) suggests ${level} turnover.`;
}

function paperEligibilityFinding(
  eligibility: PaperTradingEligibility,
  lang: Language
): string {
  if (eligibility === "eligible") {
    return lang === "zh"
      ? "基于回测质量，该策略可进入模拟试盘（paper trading）观察。"
      : "Based on backtest quality, this strategy is eligible for paper trading.";
  }
  if (eligibility === "watch") {
    return lang === "zh"
      ? "基于回测质量，建议先观察后再进入模拟试盘。"
      : "Based on backtest quality, watch before entering paper trading.";
  }
  return lang === "zh"
    ? "基于回测质量，暂不建议进入模拟试盘。"
    : "Based on backtest quality, this strategy is not eligible for paper trading yet.";
}

/** 生成 Key Findings 列表（规则解释，非 LLM） */
export function buildBacktestReviewFindings(
  result: BacktestResponse,
  lang: Language
): string[] {
  const metrics = result.metrics;
  const totalReturn = metrics.total_return;
  const benchmarkReturn = metrics.benchmark_return;
  const maxDrawdown = resolveMaxDrawdown(metrics);
  const riskLevel = calculateBacktestRiskLevel(maxDrawdown);
  const eligibility = calculatePaperTradingEligibility(riskLevel);
  const findings: string[] = [];

  if (totalReturn != null && benchmarkReturn != null) {
    const excess = totalReturn - benchmarkReturn;
    if (excess > 0.001) {
      findings.push(
        lang === "zh"
          ? `策略跑赢基准 ${formatPct(excess)}。`
          : `Strategy outperformed benchmark by ${formatPct(excess)}.`
      );
    } else if (excess < -0.001) {
      findings.push(
        lang === "zh"
          ? `策略跑输基准 ${formatPct(Math.abs(excess))}。`
          : `Strategy underperformed benchmark by ${formatPct(Math.abs(excess))}.`
      );
    } else {
      findings.push(
        lang === "zh"
          ? "策略与基准表现大致相当。"
          : "Strategy performed roughly in line with the benchmark."
      );
    }
  }

  if (maxDrawdown != null) {
    findings.push(
      lang === "zh"
        ? `最大回撤达到 ${formatPct(maxDrawdown)}，对应 ${riskLevel} 风险档位。`
        : `Max drawdown reached ${formatPct(maxDrawdown)}, which maps to ${riskLevel} risk level.`
    );
  }

  findings.push(sharpeAssessment(metrics.sharpe_ratio, lang));
  findings.push(costDragAssessment(metrics.transaction_cost_total, totalReturn, lang));
  findings.push(turnoverAssessment(metrics.number_of_trades, lang));
  findings.push(paperEligibilityFinding(eligibility, lang));

  return findings;
}

/** 管理层解读（规则模板） */
export function buildBacktestManagementInterpretation(
  result: BacktestResponse,
  riskLevel: BacktestRiskLevel,
  eligibility: PaperTradingEligibility,
  lang: Language
): string {
  const totalReturn = result.metrics.total_return;
  const positive = totalReturn != null && totalReturn > 0;

  if (lang === "zh") {
    if (eligibility === "eligible") {
      return positive
        ? "该回测显示策略具备一定模拟收益，且回撤处于可接受区间，可进入模拟试盘做进一步治理观察。"
        : "该回测收益承压，但回撤仍在较温和区间；若进入模拟试盘，应限制敞口并加强复盘。";
    }
    if (eligibility === "watch") {
      return "该回测显示策略具备一定模拟收益，但由于回撤进入 Yellow 风险区间，建议仅在限制敞口下进入模拟试盘观察。";
    }
    return `该回测回撤达到 ${riskLevel} 风险区间，模拟收益不足以支撑积极试盘；建议先优化参数或延长验证后再考虑 paper trading。`;
  }

  if (eligibility === "eligible") {
    return positive
      ? "This backtest shows positive simulated return with acceptable drawdown. Paper trading may proceed under standard governance review."
      : "Simulated return is weak, but drawdown remains contained. Any paper trading should use restricted exposure and active review.";
  }
  if (eligibility === "watch") {
    return "This backtest shows positive simulated return, but the strategy should enter paper trading only under restricted exposure because drawdown has reached Yellow risk level.";
  }
  return `Drawdown maps to ${riskLevel} risk level. Simulated return quality is insufficient for active paper trading until further validation.`;
}

/** 组装 explanationPayload（预留 LLM/RAG） */
export function buildBacktestExplanationPayload(
  result: BacktestResponse,
  lang: Language
): BacktestExplanationPayload {
  const metrics = result.metrics;
  const maxDrawdown = resolveMaxDrawdown(metrics);
  const riskLevel = calculateBacktestRiskLevel(maxDrawdown);
  const eligibility = calculatePaperTradingEligibility(riskLevel);
  const reviewFindings = buildBacktestReviewFindings(result, lang);

  const totalReturn = metrics.total_return;
  const benchmarkReturn = metrics.benchmark_return;
  const excessReturn =
    totalReturn != null && benchmarkReturn != null
      ? totalReturn - benchmarkReturn
      : null;

  return {
    strategy: result.strategy,
    symbol: result.ticker,
    totalReturn,
    benchmarkReturn,
    excessReturn,
    maxDrawdown,
    sharpeRatio: metrics.sharpe_ratio,
    tradeCount: metrics.number_of_trades,
    costPaid: metrics.transaction_cost_total,
    backtestRiskLevel: riskLevel,
    paperTradingEligibility: eligibility,
    reviewFindings,
  };
}

export function riskLevelToBadgeLevel(label: BacktestRiskLevel): number {
  switch (label) {
    case "Green":
      return 1;
    case "Light Yellow":
      return 2;
    case "Yellow":
      return 3;
    case "Orange":
      return 4;
    case "Red":
      return 5;
  }
}
