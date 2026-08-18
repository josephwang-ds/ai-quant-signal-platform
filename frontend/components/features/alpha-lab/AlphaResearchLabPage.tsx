"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import AppShell from "@/components/layout/AppShell";
import {
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import { alphaLabCopy } from "@/lib/alphaLabCopy";
import {
  FactorValidationApiError,
  fetchFactorValidation,
} from "@/lib/factorValidationApi";
import type { FactorValidationResult } from "@/types/factorValidation";

type TabId = "question" | "data" | "alpha" | "portfolio" | "attribution";

const TABS: Array<{ id: TabId; number: string; built: boolean }> = [
  { id: "question", number: "01", built: true },
  { id: "data", number: "02", built: true },
  { id: "alpha", number: "03", built: true },
  { id: "portfolio", number: "04", built: false },
  { id: "attribution", number: "05", built: false },
];

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  return `${(value * 100).toFixed(2)}%`;
}

function fmtNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "N/A";
  }
  return value.toFixed(digits);
}

function decisionFromVerdict(verdict: unknown): {
  key: "promote" | "hold" | "reject";
  tone: "positive" | "warning" | "negative";
} {
  switch (verdict) {
    case "pass":
      return { key: "promote", tone: "positive" };
    case "fail":
      return { key: "reject", tone: "negative" };
    default:
      // "partial" and "inconclusive" (and any unrecognized verdict) hold —
      // never auto-promote on ambiguous or unavailable evidence.
      return { key: "hold", tone: "warning" };
  }
}

function NotYetBuiltPanel({ title, note }: { title: string; note: string }) {
  return (
    <div className="alpha-lab__placeholder">
      <h3>{title}</h3>
      <p>{note}</p>
    </div>
  );
}

function StatSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="alpha-lab__stat-section">
      <p className="alpha-lab__stat-section-label">{title}</p>
      <div className="alpha-lab__stat-grid">{children}</div>
    </div>
  );
}

function StatCard({
  label,
  value,
  caption,
}: {
  label: string;
  value: string;
  caption?: string;
}) {
  return (
    <div className="alpha-lab__stat-card">
      <p className="alpha-lab__stat-label">{label}</p>
      <p className="alpha-lab__stat-value">{value}</p>
      {caption ? <p className="alpha-lab__stat-caption">{caption}</p> : null}
    </div>
  );
}

export default function AlphaResearchLabPage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const c = alphaLabCopy(language);
  // The fetch effect must not re-run on a language change, so it reads the
  // current language through a ref rather than closing over it.
  const languageRef = useRef(language);
  languageRef.current = language;
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading"
  );
  const [data, setData] = useState<FactorValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>("alpha");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setError(null);
    fetchFactorValidation({ signal: controller.signal })
      .then((result) => {
        if (controller.signal.aborted) return;
        setData(result);
        setStatus("ready");
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setData(null);
        setStatus("error");
        setError(
          err instanceof FactorValidationApiError
            ? err.message
            : alphaLabCopy(languageRef.current).fetchError
        );
      });
    return () => controller.abort();
  }, []);

  const verdict = data?.benchmark?.verdict;
  const decision = decisionFromVerdict(verdict);
  const decisionLabel = c.decisions[decision.key];
  const regression = data?.capm.regression;
  const decomposition = data?.capm.decomposition;

  const decompositionChart =
    decomposition?.dates.map((date, index) => ({
      date,
      betaContribution: decomposition.cumulative_beta_contribution[index]?.value,
      residualAlpha: decomposition.cumulative_residual_alpha[index]?.value,
      costDrag: -(decomposition.cumulative_cost_drag[index]?.value ?? 0),
    })) ?? [];

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
    <div className="alpha-lab">
      <header className="alpha-lab__hero">
        <div className="alpha-lab__hero-top">
          <div>
            <p className="alpha-lab__eyebrow">{c.eyebrow}</p>
            <p className="alpha-lab__breadcrumb">{c.breadcrumb}</p>
          </div>
        </div>
        <nav className="alpha-lab__tabs">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`alpha-lab__tab${tab === item.id ? " alpha-lab__tab--active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              <span className="alpha-lab__tab-number">{item.number}</span>
              <span>{c.tabs[item.id]}</span>
            </button>
          ))}
        </nav>
        <div className="alpha-lab__chain" aria-hidden="true">
          {TABS.map((item, index) => (
            <div className="alpha-lab__chain-node" key={item.id}>
              <span
                className={`alpha-lab__chain-dot${
                  item.built ? " alpha-lab__chain-dot--built" : ""
                }`}
              />
              {index < TABS.length - 1 ? (
                <span className="alpha-lab__chain-line" />
              ) : null}
            </div>
          ))}
        </div>
      </header>

      <div className="alpha-lab__title-row">
        <div>
          <p className="alpha-lab__kicker">{c.kicker}</p>
          <h1 className="alpha-lab__title">{c.title}</h1>
        </div>
        {status === "ready" ? (
          <span
            className={`alpha-lab__decision alpha-lab__decision--${decision.tone}`}
          >
            {c.decisionPrefix} · {decisionLabel}
          </span>
        ) : null}
      </div>

      <div className="alpha-lab__question-band">
        <p className="alpha-lab__question">{c.question}</p>
        {data ? (
          <p className="alpha-lab__question-meta">
            {data.universe_id} · {c.metaMonthly} ·{" "}
            {c.metaForward(data.holding_period_months)} · {c.metaChronological} ·{" "}
            {c.metaBenchmark}: {data.capm.benchmark_symbol}
          </p>
        ) : null}
        <p className="alpha-lab__scope-line">{c.scopeLine}</p>
      </div>

      {status === "loading" ? (
        <p className="alpha-lab__status">{c.loading}</p>
      ) : null}
      {status === "error" ? (
        <p className="alpha-lab__status alpha-lab__status--error">
          {error ?? c.unavailable}
        </p>
      ) : null}

      {status === "ready" && data ? (
        <>
          {tab === "alpha" ? (
            <>
              <StatSection title={c.sections.information}>
                <StatCard
                  label={c.stats.meanRankIc}
                  value={fmtNumber(data.ic.summary.mean_rank_ic, 4)}
                  caption={c.stats.meanRankIcCaption}
                />
                <StatCard
                  label={c.stats.icir}
                  value={fmtNumber(data.ic.summary.icir)}
                  caption={c.stats.icirCaption}
                />
                <StatCard
                  label={c.stats.positiveIc}
                  value={fmtPct(data.ic.summary.positive_ic_ratio)}
                  caption={c.stats.positiveIcCaption(data.ic.summary.n_periods)}
                />
              </StatSection>

              <StatSection title={c.sections.costs}>
                <StatCard
                  label={c.stats.grossSpread}
                  value={fmtPct(data.long_short.cumulative_final)}
                  caption={c.stats.grossSpreadCaption}
                />
                <StatCard
                  label={c.stats.netSpread}
                  value={fmtPct(data.long_short.cumulative_final_net_of_cost)}
                  caption={c.stats.netSpreadCaption}
                />
                <StatCard
                  label={c.stats.turnover}
                  value={fmtNumber(data.quantiles.turnover.mean)}
                  caption={c.stats.turnoverCaption}
                />
              </StatSection>

              <StatSection title={c.sections.alphaOrBeta}>
                <StatCard
                  label={c.stats.netAlpha}
                  value={fmtPct(regression?.alpha_annualized)}
                  caption={c.stats.netAlphaCaption(fmtPct(regression?.alpha_annualized_ci_low), fmtPct(regression?.alpha_annualized_ci_high))}
                />
                <StatCard
                  label={c.stats.tstat}
                  value={fmtNumber(regression?.t_stat_alpha)}
                  caption={c.stats.tstatCaption(regression?.n_observations ?? 0)}
                />
                <StatCard
                  label={c.stats.beta}
                  value={fmtNumber(regression?.beta)}
                  caption={c.stats.betaCaption(data.capm.benchmark_symbol)}
                />
                <StatCard
                  label={c.stats.rSquared}
                  value={fmtNumber(regression?.r_squared)}
                  caption={c.stats.rSquaredCaption}
                />
              </StatSection>

              <StatSection title={c.sections.stability}>
                <StatCard
                  label={c.stats.sharpe}
                  value={fmtNumber(data.portfolio_risk.sharpe_ratio_net)}
                  caption={c.stats.sharpeCaption}
                />
                <StatCard
                  label={c.stats.maxDrawdown}
                  value={fmtPct(data.portfolio_risk.max_drawdown_net)}
                  caption={c.stats.maxDrawdownCaption}
                />
              </StatSection>

              <p className="alpha-lab__provenance-note">
                {c.provenance(
                  data.universe_id,
                  data.capm.benchmark_symbol,
                  data.provenance.start_date,
                  data.provenance.end_date ?? c.dataTab.latest
                )}
              </p>

              <div className="alpha-lab__chart-panel">
                <p className="alpha-lab__chart-title">{c.chart.title}</p>
                <p className="alpha-lab__chart-subtitle">{c.chart.subtitle}</p>
                <div style={{ width: "100%", height: 300 }}>
                  <ResponsiveContainer>
                    <ComposedChart
                      data={decompositionChart}
                      margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
                    >
                      <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
                      <XAxis
                        dataKey="date"
                        hide={decompositionChart.length > 24}
                        tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                      />
                      <YAxis
                        tick={{ fill: CHART_TICK_FILL, fontSize: CHART_TICK_FONT_SIZE }}
                        tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`}
                        width={52}
                      />
                      <Tooltip {...CHART_TOOLTIP_STYLE} />
                      <Legend wrapperStyle={{ fontSize: 12, color: "var(--text-secondary)" }} />
                      <Area
                        type="monotone"
                        dataKey="costDrag"
                        name={c.chart.costDrag}
                        fill="var(--chart-series-3)"
                        stroke="var(--chart-series-3)"
                        fillOpacity={0.18}
                        strokeWidth={1}
                      />
                      <Line
                        type="monotone"
                        dataKey="betaContribution"
                        name={c.chart.betaContribution}
                        stroke="var(--chart-series-2)"
                        strokeDasharray="5 4"
                        dot={false}
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="residualAlpha"
                        name={c.chart.residualAlpha}
                        stroke="var(--chart-series-1)"
                        dot={false}
                        strokeWidth={2.5}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                <p className="alpha-lab__methodology">
                  {c.chart.methodology ?? decomposition?.methodology}
                </p>
              </div>
            </>
          ) : null}

          {tab === "question" ? (
            <div className="alpha-lab__panel">
              <h3>{c.questionTab.heading}</h3>
              <p className="alpha-lab__lede">{c.questionTab.lede}</p>
              <ol className="alpha-lab__findings">
                {c.questionTab.findings.map((finding) => (
                  <li key={finding.lead}>
                    <strong>{finding.lead}</strong> {finding.body}
                  </li>
                ))}
              </ol>
              <p>
                {c.questionTab.decisionLine(
                  decisionLabel,
                  String(verdict ?? "unavailable")
                )}
              </p>
              <p className="alpha-lab__scope-note">{c.questionTab.scopeNote}</p>
            </div>
          ) : null}

          {tab === "data" ? (
            <div className="alpha-lab__panel">
              <h3>{c.dataTab.heading}</h3>
              <dl className="alpha-lab__kv">
                <dt>{c.dataTab.universe}</dt>
                <dd>
                  {data.universe_id} (
                  {c.dataTab.universeValue(
                    data.provenance.symbols_used.length,
                    data.provenance.universe_symbols.length
                  )}
                  )
                </dd>
                <dt>{c.dataTab.dateRange}</dt>
                <dd>
                  {data.provenance.start_date} →{" "}
                  {data.provenance.end_date ?? c.dataTab.latest}
                </dd>
                <dt>{c.dataTab.factorPeriods}</dt>
                <dd>{data.provenance.n_factor_periods}</dd>
                <dt>{c.dataTab.benchmark}</dt>
                <dd>{data.provenance.benchmark_symbol}</dd>
              </dl>
              {data.warnings.length > 0 ? (
                <>
                  <h4>{c.dataTab.warnings}</h4>
                  <ul className="alpha-lab__warnings">
                    {data.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="alpha-lab__muted">{c.dataTab.noWarnings}</p>
              )}
            </div>
          ) : null}

          {tab === "portfolio" ? (
            <NotYetBuiltPanel
              title={c.notBuilt.portfolioTitle}
              note={c.notBuilt.portfolioNote}
            />
          ) : null}

          {tab === "attribution" ? (
            <NotYetBuiltPanel
              title={c.notBuilt.attributionTitle}
              note={c.notBuilt.attributionNote}
            />
          ) : null}
        </>
      ) : null}

      {status === "ready" ? (
        <p className="alpha-lab__pipeline-recap">
          {c.pipelineRecap(decisionLabel)}
        </p>
      ) : null}
    </div>
    </AppShell>
  );
}
