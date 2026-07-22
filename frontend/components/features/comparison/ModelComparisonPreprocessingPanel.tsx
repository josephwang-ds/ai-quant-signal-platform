"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ModelComparisonPreprocessing } from "@/lib/api";
import {
  CHART_COLORS,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import { translateModelFeatureName } from "@/lib/i18n";
import type { Language } from "@/lib/i18n";

export type ModelComparisonPreprocessingPanelProps = {
  preprocessing: ModelComparisonPreprocessing;
  language: Language;
  labels: {
    title: string;
    methodNone: string;
    methodPca: string;
    methodSelectKBest: string;
    methodL1: string;
    pcaCaption: string;
    pcaCumulative: string;
    selectedTitle: string;
    droppedTitle: string;
    emptySelection: string;
  };
};

function methodLabel(
  method: string,
  labels: ModelComparisonPreprocessingPanelProps["labels"]
): string {
  if (method === "pca") return labels.methodPca;
  if (method === "select_kbest") return labels.methodSelectKBest;
  if (method === "l1_select") return labels.methodL1;
  return labels.methodNone;
}

export default function ModelComparisonPreprocessingPanel({
  preprocessing,
  language,
  labels,
}: ModelComparisonPreprocessingPanelProps) {
  const method = preprocessing.method || "none";
  if (method === "none") {
    return null;
  }

  const pca = preprocessing.pca;
  const selection = preprocessing.selection;
  const pcaRows =
    pca?.explained_variance_ratio.map((ratio, index) => ({
      name: `PC${index + 1}`,
      ratio,
      cumulative: pca.explained_variance_ratio
        .slice(0, index + 1)
        .reduce((sum, value) => sum + value, 0),
    })) ?? [];

  const cumulativePct = pca
    ? Math.round(pca.cumulative * 1000) / 10
    : null;

  return (
    <section
      className="model-comparison-preprocessing"
      aria-label={labels.title}
    >
      <header className="model-comparison-preprocessing__header">
        <h3 className="model-comparison-preprocessing__title">{labels.title}</h3>
        <span className="model-comparison-preprocessing__method">
          {methodLabel(method, labels)}
        </span>
      </header>

      {pca && pcaRows.length > 0 ? (
        <div className="model-comparison-preprocessing__pca">
          <p className="model-comparison-preprocessing__caption">
            {labels.pcaCaption
              .replace("{n}", String(pca.n_components))
              .replace("{pct}", String(cumulativePct))}
          </p>
          <div className="model-comparison-preprocessing__chart">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={pcaRows} margin={{ top: 8, right: 12, left: 0, bottom: 4 }}>
                <CartesianGrid stroke={CHART_GRID_STROKE} vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                />
                <YAxis
                  tickFormatter={(value: number) => `${Math.round(value * 100)}%`}
                  tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                  domain={[0, 1]}
                />
                <Tooltip
                  {...CHART_TOOLTIP_STYLE}
                  formatter={(value, name) => {
                    const numeric = typeof value === "number" ? value : Number(value);
                    const pct = Number.isFinite(numeric)
                      ? `${(numeric * 100).toFixed(1)}%`
                      : String(value);
                    return [pct, name === "cumulative" ? labels.pcaCumulative : name];
                  }}
                />
                <Bar
                  dataKey="ratio"
                  fill={CHART_COLORS.strategy}
                  name="explained"
                  radius={[3, 3, 0, 0]}
                />
                <Line
                  type="monotone"
                  dataKey="cumulative"
                  stroke={CHART_COLORS.benchmark}
                  strokeWidth={2}
                  dot={false}
                  name="cumulative"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : null}

      {selection ? (
        <div className="model-comparison-preprocessing__selection">
          <div className="model-comparison-preprocessing__col model-comparison-preprocessing__col--kept">
            <h4>{labels.selectedTitle}</h4>
            {selection.selected_features.length === 0 ? (
              <p className="model-comparison-preprocessing__empty">
                {labels.emptySelection}
              </p>
            ) : (
              <ul>
                {selection.selected_features.map((feature) => (
                  <li key={feature}>
                    <code>{feature}</code>
                    <span>{translateModelFeatureName(language, feature)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="model-comparison-preprocessing__col model-comparison-preprocessing__col--dropped">
            <h4>{labels.droppedTitle}</h4>
            {selection.dropped_features.length === 0 ? (
              <p className="model-comparison-preprocessing__empty">
                {labels.emptySelection}
              </p>
            ) : (
              <ul>
                {selection.dropped_features.map((feature) => (
                  <li key={feature}>
                    <code>{feature}</code>
                    <span>{translateModelFeatureName(language, feature)}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}
