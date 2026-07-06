/** 仪表盘数值格式化工具 */

export function formatPrice(value: number): string {
  return value.toFixed(2);
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

export function formatRsi(value: number): string {
  return value.toFixed(1);
}

export function formatScore(value: number): string {
  return Math.round(value).toString();
}

export function formatMetricPercent(value: number | null | undefined): string {
  if (value == null) {
    return "N/A";
  }
  return `${(value * 100).toFixed(2)}%`;
}

export function formatMetricSharpe(value: number | null | undefined): string {
  if (value == null) {
    return "N/A";
  }
  return value.toFixed(2);
}

export function formatMetricTrades(value: number | null | undefined): string {
  if (value == null) {
    return "N/A";
  }
  return Math.round(value).toString();
}

export type MetricTone = "default" | "positive" | "negative" | "accent";

export function getReturnTone(value: number | null | undefined): MetricTone {
  if (value == null) {
    return "default";
  }
  if (value > 0) {
    return "positive";
  }
  if (value < 0) {
    return "negative";
  }
  return "default";
}

export function getDrawdownTone(value: number | null | undefined): MetricTone {
  if (value == null) {
    return "default";
  }
  return "negative";
}

export function getSharpeTone(value: number | null | undefined): MetricTone {
  if (value == null) {
    return "default";
  }
  if (value >= 0.5) {
    return "accent";
  }
  return "default";
}
