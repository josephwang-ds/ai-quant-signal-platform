import type { Language } from "@/lib/i18n";
import { formatMetricPercent } from "@/lib/formatters";
import { benchmarkLabel } from "@/lib/researchDisplay";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult } from "@/types/researchExecution";

export type MaWindows = {
  shortWindow: number | null;
  longWindow: number | null;
};

export type ResearchProtocolParts = {
  symbol: string | null;
  maWindows: MaWindows;
  period: string | null;
  transactionCostPct: string | null;
  benchmark: string | null;
};

function formatIsoDateShort(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const locale = language === "zh" ? "zh-CN" : "en-US";
  return date.toLocaleDateString(locale, { year: "numeric", month: "short", day: "numeric" });
}

export function parseMaWindows(
  research: ResearchDetail,
  execution: ResearchExecutionResult | null
): MaWindows {
  const shortFromExecution =
    execution && typeof (execution.strategy as { short_window?: number }).short_window === "number"
      ? (execution.strategy as { short_window: number }).short_window
      : null;
  const longFromExecution =
    execution && typeof (execution.strategy as { long_window?: number }).long_window === "number"
      ? (execution.strategy as { long_window: number }).long_window
      : null;
  if (typeof shortFromExecution === "number" && typeof longFromExecution === "number") {
    return { shortWindow: shortFromExecution, longWindow: longFromExecution };
  }

  const parameterLines = research.configuration?.parameterLines ?? [];
  const shortMatch = parameterLines
    .map((line) => line.trim())
    .find((line) => /^Short Window\s*:/i.test(line));
  const longMatch = parameterLines
    .map((line) => line.trim())
    .find((line) => /^Long Window\s*:/i.test(line));
  const shortWindow = shortMatch ? Number(shortMatch.replace(/[^\d]/g, "")) : null;
  const longWindow = longMatch ? Number(longMatch.replace(/[^\d]/g, "")) : null;
  return { shortWindow, longWindow };
}

export function parseTransactionCost(
  research: ResearchDetail
): number | null {
  if (typeof research.runConfiguration?.transactionCost === "number") {
    return research.runConfiguration.transactionCost;
  }
  const match = research.configuration.parameterLines
    ?.join("\n")
    .match(/Transaction Cost\s*:\s*([0-9.]+)/i);
  return match ? Number(match[1]) : null;
}

export function buildResearchProtocolParts(
  research: ResearchDetail,
  execution: ResearchExecutionResult | null,
  language: Language
): ResearchProtocolParts {
  const symbol =
    execution?.provenance?.symbol ??
    research.runConfiguration?.symbol ??
    research.configuration.symbol ??
    null;

  const maWindows = parseMaWindows(research, execution);

  const period =
    execution?.provenance?.actual_start && execution?.provenance?.actual_end
      ? `${formatIsoDateShort(execution.provenance.actual_start, language)} → ${formatIsoDateShort(execution.provenance.actual_end, language)}`
      : research.runConfiguration
        ? `${formatIsoDateShort(research.runConfiguration.startDate, language)} → ${
            research.runConfiguration.endDate
              ? formatIsoDateShort(research.runConfiguration.endDate, language)
              : language === "zh"
                ? "至今"
                : "Present"
          }`
        : null;

  const transactionCost = parseTransactionCost(research);
  const transactionCostPct =
    typeof transactionCost === "number" && Number.isFinite(transactionCost)
      ? formatMetricPercent(transactionCost)
      : null;

  const benchmarkRaw =
    research.runConfiguration?.benchmark ??
    research.configuration.benchmark ??
    null;
  const benchmark = benchmarkRaw ? benchmarkLabel(benchmarkRaw, language) : null;

  return {
    symbol,
    maWindows,
    period,
    transactionCostPct,
    benchmark,
  };
}

export function formatResearchProtocolLine(
  parts: ResearchProtocolParts,
  language: Language
): string | null {
  const maPart =
    typeof parts.maWindows.shortWindow === "number" &&
    typeof parts.maWindows.longWindow === "number"
      ? `MA${parts.maWindows.shortWindow}/MA${parts.maWindows.longWindow}`
      : null;

  const costPart = parts.transactionCostPct
    ? language === "zh"
      ? `成本 ${parts.transactionCostPct}`
      : `Cost ${parts.transactionCostPct}`
    : null;

  const segments = [
    parts.symbol,
    maPart,
    parts.period,
    costPart,
    parts.benchmark,
  ].filter(Boolean);

  return segments.length ? segments.join(" · ") : null;
}
