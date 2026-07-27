"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import MetricSummaryCard from "@/components/ui/MetricSummaryCard";
import type {
  FeatureImportanceMethodBlock,
  FeatureImportanceResearch,
  ModelComparisonResult,
} from "@/lib/api";
import {
  CHART_COLORS,
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import { translateModelFeatureName, type Language } from "@/lib/i18n";

const CAUSALITY = "Feature importance does not imply causality.";

type Labels = {
  disclaimer: string;
  rankingTitle: string;
  methodNative: string;
  methodPermutation: string;
  methodShap: string;
  methodCoefficient: string;
  unavailable: string;
  consistentTitle: string;
  unstableTitle: string;
  consistentEmpty: string;
  unstableEmpty: string;
  stabilityNote: string;
  stabilityNeedFolds: string;
  stabilityUnavailable: string;
  foldCount: string;
  signedCoef: string;
  limitationsTitle: string;
};

type Props = {
  results: ModelComparisonResult[];
  language: Language;
  labels: Labels;
};

function methodEntries(
  block: FeatureImportanceMethodBlock | undefined,
  language: Language
): { name: string; value: number }[] {
  if (!block?.available || !block.values) return [];
  return Object.entries(block.values)
    .map(([feature, value]) => ({
      name: translateModelFeatureName(language, feature),
      value,
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 12);
}

function MethodChart({
  title,
  block,
  language,
  unavailable,
}: {
  title: string;
  block: FeatureImportanceMethodBlock | undefined;
  language: Language;
  unavailable: string;
}) {
  const rows = methodEntries(block, language);
  return (
    <div className="chart-panel">
      <h3 className="chart-panel__title">{title}</h3>
      {block?.note ? <p className="section-meta">{block.note}</p> : null}
      {rows.length === 0 ? (
        <p className="section-meta">{unavailable}</p>
      ) : (
        <div className="chart-panel__body" style={{ width: "100%", height: 280 }}>
          <ResponsiveContainer>
            <BarChart
              layout="vertical"
              data={rows}
              margin={{ top: 8, right: 16, left: 8, bottom: 8 }}
            >
              <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
              <XAxis
                type="number"
                tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                tickFormatter={(v) => Number(v).toFixed(2)}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fill: CHART_TICK_FILL, fontSize: 11 }}
              />
              <Tooltip
                {...CHART_TOOLTIP_STYLE}
                formatter={(value) => Number(value).toFixed(4)}
              />
              <Bar
                dataKey="value"
                fill={CHART_COLORS.strategy}
                radius={[0, 2, 2, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function ModelInterpretationCard({
  row,
  language,
  labels,
}: {
  row: ModelComparisonResult;
  language: Language;
  labels: Labels;
}) {
  const research = row.importance_research as FeatureImportanceResearch | undefined;
  if (!research) {
    return (
      <section className="feature-interpretation-model">
        <h3>{row.label}</h3>
        <p className="section-meta">{labels.unavailable}</p>
      </section>
    );
  }

  const methods = research.methods ?? {};
  const stability = research.stability;
  const ranking = research.ranking ?? [];

  return (
    <section className="feature-interpretation-model">
      <header className="feature-interpretation-model__header">
        <h3>{row.label}</h3>
        <p className="feature-interpretation-disclaimer">
          {research.disclaimer || labels.disclaimer || CAUSALITY}
        </p>
      </header>

      <div className="feature-interpretation-methods">
        <MethodChart
          title={labels.methodShap}
          block={methods.shap}
          language={language}
          unavailable={labels.unavailable}
        />
        <MethodChart
          title={labels.methodPermutation}
          block={methods.permutation}
          language={language}
          unavailable={labels.unavailable}
        />
        <MethodChart
          title={labels.methodCoefficient}
          block={methods.coefficient}
          language={language}
          unavailable={labels.unavailable}
        />
        <MethodChart
          title={labels.methodNative}
          block={methods.native}
          language={language}
          unavailable={labels.unavailable}
        />
      </div>

      <div className="feature-interpretation-ranking">
        <h4>{labels.rankingTitle}</h4>
        {ranking.length === 0 ? (
          <p className="section-meta">{labels.unavailable}</p>
        ) : (
          <ol className="feature-interpretation-ranking__list">
            {ranking.slice(0, 10).map((item) => (
              <li key={`${item.feature}-${item.rank}`}>
                <span>
                  {translateModelFeatureName(language, item.feature)}
                </span>
                <span>
                  {item.score.toFixed(4)} · {item.method}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>

      {methods.coefficient?.available && methods.coefficient.signed ? (
        <div className="feature-interpretation-signed">
          <h4>{labels.signedCoef}</h4>
          <ul className="feature-interpretation-ranking__list">
            {Object.entries(methods.coefficient.signed)
              .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
              .slice(0, 8)
              .map(([feature, value]) => (
                <li key={feature}>
                  <span>{translateModelFeatureName(language, feature)}</span>
                  <span>{value.toFixed(4)}</span>
                </li>
              ))}
          </ul>
        </div>
      ) : null}

      {(research.limitations?.length ?? 0) > 0 ? (
        <div className="feature-interpretation-limitations">
          <h4>{labels.limitationsTitle}</h4>
          <ul>
            {research.limitations!.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="feature-interpretation-stability">
        <div className="metric-summary-grid">
          <MetricSummaryCard
            label={labels.foldCount}
            value={
              stability?.available
                ? String(stability.n_folds)
                : labels.stabilityNeedFolds
            }
          />
        </div>
        <p className="section-meta">
          {stability?.available
            ? stability.note || labels.stabilityNote
            : labels.stabilityNeedFolds}
        </p>
        {stability?.available ? (
          <div className="feature-interpretation-stability__columns">
            <div>
              <h4>{labels.consistentTitle}</h4>
              {(stability.consistent_features?.length ?? 0) === 0 ? (
                <p className="section-meta">{labels.consistentEmpty}</p>
              ) : (
                <ul>
                  {stability.consistent_features.map((feature) => (
                    <li key={feature}>
                      {translateModelFeatureName(language, feature)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h4>{labels.unstableTitle}</h4>
              {(stability.unstable_features?.length ?? 0) === 0 ? (
                <p className="section-meta">{labels.unstableEmpty}</p>
              ) : (
                <ul>
                  {stability.unstable_features.map((feature) => (
                    <li key={feature}>
                      {translateModelFeatureName(language, feature)}
                      {stability.per_feature?.[feature]?.cv != null
                        ? ` (CV ${stability.per_feature[feature].cv!.toFixed(2)})`
                        : ""}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        ) : (
          <p className="section-meta">{labels.stabilityUnavailable}</p>
        )}
      </div>
    </section>
  );
}

export default function FeatureInterpretationPanels({
  results,
  language,
  labels,
}: Props) {
  const mlRows = results.filter(
    (row) => row.kind === "ml" && row.uses_features !== false
  );

  if (mlRows.length === 0) {
    return <p className="section-meta">{labels.unavailable}</p>;
  }

  return (
    <div className="feature-interpretation-panels">
      <p className="feature-interpretation-disclaimer feature-interpretation-disclaimer--page">
        {labels.disclaimer}
      </p>
      {mlRows.map((row) => (
        <ModelInterpretationCard
          key={row.strategy || row.label}
          row={row}
          language={language}
          labels={labels}
        />
      ))}
    </div>
  );
}
