"use client";

import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import EmptyState from "@/components/ui/EmptyState";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import type {
  ModelComparisonEquityRow,
  ModelComparisonFold,
  ModelComparisonResponse,
  ModelComparisonResult,
} from "@/lib/api";
import {
  CHART_COLORS,
  CHART_COMPARE_LINES,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import {
  formatMetricPercent,
  formatMetricSharpe,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import {
  translateComparisonLabel,
  translateModelFeatureName,
  type Language,
} from "@/lib/i18n";

const BUY_HOLD_LABEL = "Buy & Hold";
const BAR_EMPHASIS = CHART_COLORS.strategy;
const BAR_MUTED = "#94a3b8";
const ML_SCATTER = CHART_COMPARE_LINES[0];
const RULE_SCATTER = CHART_COMPARE_LINES[1];

type ChartLabels = {
  championSharpe: string;
  championReturn: string;
  championDrawdown: string;
  championModel: string;
  totalReturn: string;
  sharpe: string;
  maxDrawdown: string;
  directionalAccuracy: string;
  equityTitle: string;
  equityEmpty: string;
  riskReturnTitle: string;
  riskReturnHint: string;
  riskReturnX: string;
  riskReturnY: string;
  riskReturnEmpty: string;
  rankTitle: string;
  rankSharpe: string;
  rankReturn: string;
  rankDrawdown: string;
  featureFocusTitle: string;
  featureEmpty: string;
  kindMl: string;
  kindRule: string;
  na: string;
  foldStabilityTitle: string;
  foldStabilityEmpty: string;
  foldStabilityYSharpe: string;
  foldStabilityYAccuracy: string;
  foldIndexLabel: string;
  offlineBadge: string;
  offlineBadgeWithDate: string;
  offlineTooltip: string;
};

type ModelComparisonChartsProps = {
  result: ModelComparisonResponse;
  language: Language;
  labels: ChartLabels;
};

function drawdownOf(row: ModelComparisonResult): number | null {
  const value = row.metrics.strategy_max_drawdown ?? row.metrics.max_drawdown;
  return value == null ? null : value;
}

function findByLabel(
  results: ModelComparisonResult[],
  label: string | null
): ModelComparisonResult | undefined {
  if (!label) return undefined;
  return results.find((row) => row.label === label);
}

function isOfflineArtifactRow(row: ModelComparisonResult): boolean {
  return row.source === "offline_artifact" || row.strategy === "lstm";
}

function offlineBadgeText(
  row: ModelComparisonResult,
  labels: Pick<ChartLabels, "offlineBadge" | "offlineBadgeWithDate">
): string {
  const trainedAt = row.trained_at?.trim();
  if (!trainedAt) return labels.offlineBadge;
  const date = trainedAt.slice(0, 10);
  return labels.offlineBadgeWithDate.replace("{date}", date);
}

function OfflineBadge({
  row,
  labels,
}: {
  row: ModelComparisonResult;
  labels: Pick<
    ChartLabels,
    "offlineBadge" | "offlineBadgeWithDate" | "offlineTooltip"
  >;
}) {
  if (!isOfflineArtifactRow(row)) return null;
  return (
    <span
      className="model-comparison-offline-badge"
      title={labels.offlineTooltip}
    >
      {offlineBadgeText(row, labels)}
    </span>
  );
}

function buildChampionBanner(
  result: ModelComparisonResponse,
  language: Language,
  labels: ChartLabels
): string {
  const bestSharpeRow = findByLabel(result.results, result.summary.best_sharpe);
  const sharpeLabel = result.summary.best_sharpe
    ? translateComparisonLabel(language, result.summary.best_sharpe)
    : labels.na;
  const sharpeValue = formatMetricSharpe(bestSharpeRow?.metrics.sharpe_ratio);
  const returnLabel = result.summary.best_total_return
    ? translateComparisonLabel(language, result.summary.best_total_return)
    : labels.na;
  const drawdownLabel = result.summary.lowest_drawdown
    ? translateComparisonLabel(language, result.summary.lowest_drawdown)
    : labels.na;

  return `${labels.championSharpe}：${sharpeLabel}（${sharpeValue}）｜${labels.championReturn}：${returnLabel}｜${labels.championDrawdown}：${drawdownLabel}`;
}

function EquityOverlayChart({
  rows,
  series,
  title,
  subtitle,
  emptyMessage,
  language,
  offlineByLabel,
  offlineTooltip,
}: {
  rows: ModelComparisonEquityRow[];
  series: string[];
  title: string;
  subtitle: string;
  emptyMessage: string;
  language: Language;
  offlineByLabel: Record<string, string>;
  offlineTooltip: string;
}) {
  if (rows.length === 0 || series.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <div className="chart-panel">
      <h3 className="chart-panel__title">{title}</h3>
      <p className="chart-caption">{subtitle}</p>
      {Object.keys(offlineByLabel).length > 0 ? (
        <p className="chart-caption model-comparison-offline-note" title={offlineTooltip}>
          {Object.entries(offlineByLabel)
            .map(
              ([label, badge]) =>
                `${translateComparisonLabel(language, label)} · ${badge}`
            )
            .join(" · ")}
        </p>
      ) : null}
      <div className="chart-panel__container chart-panel__container--md">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
              minTickGap={32}
            />
            <YAxis
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
              domain={["auto", "auto"]}
              width={48}
            />
            <Tooltip
              {...CHART_TOOLTIP_STYLE}
              formatter={(value: number) =>
                typeof value === "number" ? value.toFixed(3) : value
              }
            />
            <Legend
              wrapperStyle={{ fontSize: "0.875rem", color: CHART_TICK_FILL }}
              formatter={(value) => {
                const name = translateComparisonLabel(language, String(value));
                const badge = offlineByLabel[String(value)];
                return badge ? `${name} (${badge})` : name;
              }}
            />
            {series.map((label, index) => {
              const isBuyHold = label === BUY_HOLD_LABEL;
              return (
                <Line
                  key={label}
                  type="monotone"
                  dataKey={label}
                  name={label}
                  stroke={
                    isBuyHold
                      ? CHART_COLORS.benchmark
                      : CHART_COMPARE_LINES[index % CHART_COMPARE_LINES.length]
                  }
                  strokeDasharray={isBuyHold ? "5 4" : undefined}
                  strokeWidth={isBuyHold ? 1.75 : 1.5}
                  dot={false}
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type ScatterPoint = {
  label: string;
  displayLabel: string;
  kind: "ml" | "rule";
  drawdownPct: number;
  returnPct: number;
  isChampion: boolean;
  isBuyHold: boolean;
};

function RiskReturnScatter({
  points,
  labels,
}: {
  points: ScatterPoint[];
  labels: ChartLabels;
}) {
  if (points.length === 0) {
    return <EmptyState message={labels.riskReturnEmpty} />;
  }

  const mlPoints = points.filter((p) => p.kind === "ml");
  const rulePoints = points.filter((p) => p.kind === "rule" && !p.isBuyHold);
  const buyHoldPoints = points.filter((p) => p.isBuyHold);

  return (
    <div className="chart-panel">
      <h3 className="chart-panel__title">{labels.riskReturnTitle}</h3>
      <p className="chart-caption">{labels.riskReturnHint}</p>
      <div className="chart-panel__container chart-panel__container--md">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 12, right: 24, left: 8, bottom: 12 }}>
            <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="drawdownPct"
              name={labels.riskReturnX}
              unit="%"
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
              label={{
                value: labels.riskReturnX,
                position: "insideBottom",
                offset: -4,
                fill: CHART_TICK_FILL,
                fontSize: CHART_TICK_FONT_SIZE,
              }}
            />
            <YAxis
              type="number"
              dataKey="returnPct"
              name={labels.riskReturnY}
              unit="%"
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
              label={{
                value: labels.riskReturnY,
                angle: -90,
                position: "insideLeft",
                fill: CHART_TICK_FILL,
                fontSize: CHART_TICK_FONT_SIZE,
              }}
              width={56}
            />
            <ZAxis type="number" dataKey="z" range={[50, 220]} />
            <Tooltip
              {...CHART_TOOLTIP_STYLE}
              cursor={{ strokeDasharray: "3 3" }}
              formatter={(value: number, name: string) => [
                formatMetricPercent(Number(value) / 100),
                name === "drawdownPct" || name === labels.riskReturnX
                  ? labels.riskReturnX
                  : labels.riskReturnY,
              ]}
              labelFormatter={(_, payload) => {
                const point = payload?.[0]?.payload as ScatterPoint | undefined;
                return point?.displayLabel ?? "";
              }}
            />
            <Legend wrapperStyle={{ fontSize: "0.875rem", color: CHART_TICK_FILL }} />
            <Scatter
              name={labels.kindMl}
              data={mlPoints.map((point) => ({
                ...point,
                z: point.isChampion ? 220 : 90,
              }))}
              fill={ML_SCATTER}
              shape="circle"
            >
              <LabelList
                dataKey="displayLabel"
                position="top"
                fontSize={11}
                fill={CHART_TICK_FILL}
                content={(rawProps) => {
                  const props = rawProps as {
                    x?: number | string;
                    y?: number | string;
                    payload?: ScatterPoint;
                  };
                  if (!props.payload?.isChampion) return null;
                  const y =
                    typeof props.y === "number" ? props.y - 10 : props.y;
                  return (
                    <text
                      x={props.x}
                      y={y}
                      textAnchor="middle"
                      fill={CHART_TICK_FILL}
                      fontSize={11}
                    >
                      {props.payload.displayLabel}
                    </text>
                  );
                }}
              />
            </Scatter>
            <Scatter
              name={labels.kindRule}
              data={rulePoints.map((point) => ({
                ...point,
                z: point.isChampion ? 220 : 90,
              }))}
              fill={RULE_SCATTER}
              shape="triangle"
            >
              <LabelList
                dataKey="displayLabel"
                position="top"
                fontSize={11}
                fill={CHART_TICK_FILL}
                content={(rawProps) => {
                  const props = rawProps as {
                    x?: number | string;
                    y?: number | string;
                    payload?: ScatterPoint;
                  };
                  if (!props.payload?.isChampion) return null;
                  const y =
                    typeof props.y === "number" ? props.y - 10 : props.y;
                  return (
                    <text
                      x={props.x}
                      y={y}
                      textAnchor="middle"
                      fill={CHART_TICK_FILL}
                      fontSize={11}
                    >
                      {props.payload.displayLabel}
                    </text>
                  );
                }}
              />
            </Scatter>
            {buyHoldPoints.length > 0 ? (
              <Scatter
                name={BUY_HOLD_LABEL}
                data={buyHoldPoints.map((point) => ({ ...point, z: 120 }))}
                fill={CHART_COLORS.benchmark}
                shape="diamond"
              >
                <LabelList
                  dataKey="displayLabel"
                  position="right"
                  fontSize={11}
                  fill={CHART_TICK_FILL}
                />
              </Scatter>
            ) : null}
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

type RankRow = {
  label: string;
  displayLabel: string;
  value: number;
  isBest: boolean;
};

function RankBarChart({
  title,
  rows,
  valueFormatter,
}: {
  title: string;
  rows: RankRow[];
  valueFormatter: (value: number) => string;
}) {
  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="model-comparison-rank-chart">
      <h4 className="model-comparison-rank-chart__title">{title}</h4>
      <div className="model-comparison-rank-chart__container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ top: 4, right: 48, left: 4, bottom: 4 }}
          >
            <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
            />
            <YAxis
              type="category"
              dataKey="displayLabel"
              width={110}
              tick={{ fill: CHART_TICK_FILL, fontSize: 11 }}
            />
            <Tooltip
              {...CHART_TOOLTIP_STYLE}
              formatter={(value: number) => valueFormatter(value)}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {rows.map((row) => (
                <Cell
                  key={row.label}
                  fill={row.isBest ? BAR_EMPHASIS : BAR_MUTED}
                />
              ))}
              <LabelList
                dataKey="value"
                position="right"
                formatter={(value: number) => valueFormatter(value)}
                fontSize={11}
                fill={CHART_TICK_FILL}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function FeatureImportanceCharts({
  mlRows,
  language,
  title,
  emptyMessage,
}: {
  mlRows: ModelComparisonResult[];
  language: Language;
  title: string;
  emptyMessage: string;
}) {
  const withImportance = mlRows.filter(
    (row) => row.feature_importance && Object.keys(row.feature_importance).length > 0
  );

  if (withImportance.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <section aria-label={title}>
      <h3 className="model-comparison-section-title">{title}</h3>
      <div className="model-comparison-importance-grid">
        {withImportance.map((row) => {
          const entries = Object.entries(row.feature_importance ?? {})
            .sort((a, b) => b[1] - a[1])
            .map(([feature, value]) => ({
              feature,
              name: translateModelFeatureName(language, feature),
              value,
            }));
          return (
            <div key={`importance-${row.strategy}`} className="model-comparison-importance">
              <h4 className="model-comparison-importance__title">
                {translateComparisonLabel(language, row.label)}
              </h4>
              <div className="model-comparison-importance__chart">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={entries}
                    layout="vertical"
                    margin={{ top: 4, right: 16, left: 4, bottom: 4 }}
                  >
                    <XAxis type="number" hide />
                    <YAxis
                      type="category"
                      dataKey="name"
                      width={96}
                      tick={{ fill: CHART_TICK_FILL, fontSize: 11 }}
                    />
                    <Tooltip
                      {...CHART_TOOLTIP_STYLE}
                      formatter={(value: number) => value.toFixed(3)}
                    />
                    <Bar dataKey="value" fill={CHART_COLORS.strategy} radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function FoldStabilityChart({
  folds,
  language,
  labels,
}: {
  folds: ModelComparisonFold[];
  language: Language;
  labels: ChartLabels;
}) {
  const [metric, setMetric] = useState<"sharpe" | "accuracy">("sharpe");

  const activeFolds = folds.filter(
    (fold) => !fold.skipped && fold.per_model.length > 0
  );
  const seriesLabels = Array.from(
    new Set(activeFolds.flatMap((fold) => fold.per_model.map((item) => item.label)))
  );

  const rows = activeFolds.map((fold) => {
    const row: Record<string, string | number> = {
      fold: fold.index + 1,
    };
    for (const item of fold.per_model) {
      const value =
        metric === "sharpe" ? item.sharpe_ratio : item.directional_accuracy;
      if (value != null && Number.isFinite(value)) {
        row[item.label] = value;
      }
    }
    return row;
  });

  if (rows.length === 0 || seriesLabels.length === 0) {
    return <EmptyState message={labels.foldStabilityEmpty} />;
  }

  return (
    <div className="chart-panel">
      <div className="model-comparison-rank-header">
        <h3 className="chart-panel__title">{labels.foldStabilityTitle}</h3>
        <div className="model-comparison-view-toggle" role="group">
          <button
            type="button"
            className={`model-comparison-view-toggle__btn${
              metric === "sharpe" ? " is-active" : ""
            }`}
            aria-pressed={metric === "sharpe"}
            onClick={() => setMetric("sharpe")}
          >
            {labels.foldStabilityYSharpe}
          </button>
          <button
            type="button"
            className={`model-comparison-view-toggle__btn${
              metric === "accuracy" ? " is-active" : ""
            }`}
            aria-pressed={metric === "accuracy"}
            onClick={() => setMetric("accuracy")}
          >
            {labels.foldStabilityYAccuracy}
          </button>
        </div>
      </div>
      <div className="chart-panel__container chart-panel__container--md">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
            <XAxis
              dataKey="fold"
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
              allowDecimals={false}
              label={{
                value: labels.foldIndexLabel,
                position: "insideBottom",
                offset: -2,
                fill: CHART_TICK_FILL,
                fontSize: CHART_TICK_FONT_SIZE,
              }}
            />
            <YAxis
              tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
              width={48}
            />
            <Tooltip
              {...CHART_TOOLTIP_STYLE}
              labelFormatter={(value) => `${labels.foldIndexLabel} ${value}`}
              formatter={(value: number, name: string) => [
                metric === "accuracy"
                  ? formatMetricPercent(value)
                  : formatMetricSharpe(value),
                translateComparisonLabel(language, name),
              ]}
            />
            <Legend
              wrapperStyle={{ fontSize: "0.875rem", color: CHART_TICK_FILL }}
              formatter={(value) => translateComparisonLabel(language, String(value))}
            />
            {seriesLabels.map((label, index) => (
              <Line
                key={label}
                type="monotone"
                dataKey={label}
                name={label}
                stroke={CHART_COMPARE_LINES[index % CHART_COMPARE_LINES.length]}
                strokeWidth={2}
                dot={{ r: 3 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function ModelComparisonCharts({
  result,
  language,
  labels,
}: ModelComparisonChartsProps) {
  const [rankMetric, setRankMetric] = useState<"sharpe" | "return" | "drawdown">(
    "sharpe"
  );

  const championLabel = result.summary.best_sharpe;
  const champion = findByLabel(result.results, championLabel);
  const championDd = champion ? drawdownOf(champion) : null;

  const equityRows = result.equity_curve_rows ?? [];
  const equityLabels = result.equity_curve_labels ?? [];
  const isWalkForward = result.mode === "walk_forward";
  const folds = result.folds ?? [];
  const equitySubtitle = isWalkForward
    ? `${result.oos_start ?? result.test_start} – ${result.oos_end ?? result.test_end}`
    : `${result.test_start} – ${result.test_end}`;

  const scatterPoints: ScatterPoint[] = result.results.flatMap((row) => {
    const dd = drawdownOf(row);
    const totalReturn = row.metrics.total_return;
    if (dd == null || totalReturn == null) return [];
    return [
      {
        label: row.label,
        displayLabel: translateComparisonLabel(language, row.label),
        kind: row.kind,
        drawdownPct: Math.abs(dd) * 100,
        returnPct: totalReturn * 100,
        isChampion: row.label === championLabel,
        isBuyHold: row.strategy === "buy_and_hold" || row.label === BUY_HOLD_LABEL,
      },
    ];
  });

  const sharpeRanks: RankRow[] = [...result.results]
    .filter((row) => row.metrics.sharpe_ratio != null)
    .sort((a, b) => (b.metrics.sharpe_ratio ?? 0) - (a.metrics.sharpe_ratio ?? 0))
    .map((row, index) => ({
      label: row.label,
      displayLabel: `${translateComparisonLabel(language, row.label)}${
        isOfflineArtifactRow(row) ? ` · ${offlineBadgeText(row, labels)}` : ""
      }`,
      value: row.metrics.sharpe_ratio ?? 0,
      isBest: index === 0,
    }));

  const returnRanks: RankRow[] = [...result.results]
    .filter((row) => row.metrics.total_return != null)
    .sort((a, b) => (b.metrics.total_return ?? 0) - (a.metrics.total_return ?? 0))
    .map((row, index) => ({
      label: row.label,
      displayLabel: `${translateComparisonLabel(language, row.label)}${
        isOfflineArtifactRow(row) ? ` · ${offlineBadgeText(row, labels)}` : ""
      }`,
      value: (row.metrics.total_return ?? 0) * 100,
      isBest: index === 0,
    }));

  const drawdownRanks: RankRow[] = [...result.results]
    .filter((row) => drawdownOf(row) != null)
    .sort((a, b) => Math.abs(drawdownOf(a) ?? 0) - Math.abs(drawdownOf(b) ?? 0))
    .map((row, index) => ({
      label: row.label,
      displayLabel: `${translateComparisonLabel(language, row.label)}${
        isOfflineArtifactRow(row) ? ` · ${offlineBadgeText(row, labels)}` : ""
      }`,
      value: Math.abs(drawdownOf(row) ?? 0) * 100,
      isBest: index === 0,
    }));

  const activeRanks =
    rankMetric === "sharpe"
      ? sharpeRanks
      : rankMetric === "return"
        ? returnRanks
        : drawdownRanks;
  const activeRankTitle =
    rankMetric === "sharpe"
      ? labels.rankSharpe
      : rankMetric === "return"
        ? labels.rankReturn
        : labels.rankDrawdown;
  const activeRankFormatter =
    rankMetric === "sharpe"
      ? (value: number) => formatMetricSharpe(value)
      : (value: number) => formatMetricPercent(value / 100);

  const mlRows = result.results.filter((row) => row.kind === "ml");
  const banner = buildChampionBanner(result, language, labels);
  const offlineByLabel: Record<string, string> = {};
  for (const row of result.results) {
    if (isOfflineArtifactRow(row)) {
      offlineByLabel[row.label] = offlineBadgeText(row, labels);
    }
  }

  return (
    <div className="model-comparison-charts">
      <div className="model-comparison-champion" role="status">
        <p className="model-comparison-champion__banner">{banner}</p>
        {champion ? (
          <div className="model-comparison-champion__metrics" role="list">
            <MetricSummaryCard
              label={labels.totalReturn}
              value={formatMetricPercent(champion.metrics.total_return)}
              description={`${labels.championModel}：${translateComparisonLabel(language, champion.label)}`}
              tone={getReturnTone(champion.metrics.total_return)}
            />
            <MetricSummaryCard
              label={labels.sharpe}
              value={formatMetricSharpe(champion.metrics.sharpe_ratio)}
              tone={getSharpeTone(champion.metrics.sharpe_ratio)}
            />
            <MetricSummaryCard
              label={labels.maxDrawdown}
              value={formatMetricPercent(championDd)}
              tone={getDrawdownTone(championDd)}
            />
            <MetricSummaryCard
              label={labels.directionalAccuracy}
              value={
                champion.directional_accuracy != null
                  ? formatMetricPercent(champion.directional_accuracy)
                  : labels.na
              }
            />
            {isOfflineArtifactRow(champion) ? (
              <div className="model-comparison-champion__offline">
                <OfflineBadge row={champion} labels={labels} />
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      <EquityOverlayChart
        rows={equityRows}
        series={equityLabels}
        title={labels.equityTitle}
        subtitle={equitySubtitle}
        emptyMessage={labels.equityEmpty}
        language={language}
        offlineByLabel={offlineByLabel}
        offlineTooltip={labels.offlineTooltip}
      />

      {isWalkForward ? (
        <FoldStabilityChart folds={folds} language={language} labels={labels} />
      ) : null}

      <RiskReturnScatter points={scatterPoints} labels={labels} />

      <div className="chart-panel">
        <div className="model-comparison-rank-header">
          <h3 className="chart-panel__title">{labels.rankTitle}</h3>
          <div className="model-comparison-view-toggle" role="group">
            {(
              [
                ["sharpe", labels.rankSharpe],
                ["return", labels.rankReturn],
                ["drawdown", labels.rankDrawdown],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`model-comparison-view-toggle__btn${
                  rankMetric === id ? " is-active" : ""
                }`}
                aria-pressed={rankMetric === id}
                onClick={() => setRankMetric(id)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        <RankBarChart
          title={activeRankTitle}
          rows={activeRanks}
          valueFormatter={activeRankFormatter}
        />
      </div>

      <FeatureImportanceCharts
        mlRows={mlRows}
        language={language}
        title={labels.featureFocusTitle}
        emptyMessage={labels.featureEmpty}
      />
    </div>
  );
}
