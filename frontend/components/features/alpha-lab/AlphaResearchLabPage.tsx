"use client";

import { useEffect, useState, type ReactNode } from "react";
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
import {
  CHART_GRID_STROKE,
  CHART_TICK_FILL,
  CHART_TICK_FONT_SIZE,
  CHART_TOOLTIP_STYLE,
} from "@/lib/chartTheme";
import {
  FactorValidationApiError,
  fetchFactorValidation,
} from "@/lib/factorValidationApi";
import type { FactorValidationResult } from "@/types/factorValidation";

type TabId = "question" | "data" | "alpha" | "portfolio" | "attribution";

const TABS: Array<{
  id: TabId;
  number: string;
  label: string;
  built: boolean;
}> = [
  { id: "question", number: "01", label: "Research question", built: true },
  { id: "data", number: "02", label: "Data & signals", built: true },
  { id: "alpha", number: "03", label: "Alpha validation", built: true },
  { id: "portfolio", number: "04", label: "Portfolio & beta", built: false },
  {
    id: "attribution",
    number: "05",
    label: "Attribution & monitor",
    built: false,
  },
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
  label: string;
  tone: "positive" | "warning" | "negative";
} {
  switch (verdict) {
    case "pass":
      return { label: "Promote", tone: "positive" };
    case "fail":
      return { label: "Reject", tone: "negative" };
    default:
      // "partial" and "inconclusive" (and any unrecognized verdict) hold —
      // never auto-promote on ambiguous or unavailable evidence.
      return { label: "Hold", tone: "warning" };
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
            : "Factor validation is unavailable. Invented evidence is not shown."
        );
      });
    return () => controller.abort();
  }, []);

  const verdict = data?.benchmark?.verdict;
  const decision = decisionFromVerdict(verdict);
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
    <div className="alpha-lab">
      <header className="alpha-lab__hero">
        <div className="alpha-lab__hero-top">
          <div>
            <p className="alpha-lab__eyebrow">Alpha Research Lab</p>
            <p className="alpha-lab__breadcrumb">Signal → Attribution</p>
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
              <span>{item.label}</span>
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
          <p className="alpha-lab__kicker">Cross-sectional equity research</p>
          <h1 className="alpha-lab__title">Momentum alpha after beta and costs</h1>
        </div>
        {status === "ready" ? (
          <span
            className={`alpha-lab__decision alpha-lab__decision--${decision.tone}`}
          >
            Decision · {decision.label}
          </span>
        ) : null}
      </div>

      <div className="alpha-lab__question-band">
        <p className="alpha-lab__question">
          Does momentum retain predictive power after neutralizing market beta and
          charging turnover costs?
        </p>
        {data ? (
          <p className="alpha-lab__question-meta">
            {data.universe_id} · Monthly rebalance · Forward {data.holding_period_months}M
            return · Chronological, no shuffling · Benchmark: {data.capm.benchmark_symbol}
          </p>
        ) : null}
        <p className="alpha-lab__scope-line">
          For systematic research — not individual stock advice
        </p>
      </div>

      {status === "loading" ? (
        <p className="alpha-lab__status">Loading real factor-validation evidence…</p>
      ) : null}
      {status === "error" ? (
        <p className="alpha-lab__status alpha-lab__status--error">
          {error ?? "Unavailable."}
        </p>
      ) : null}

      {status === "ready" && data ? (
        <>
          {tab === "alpha" ? (
            <>
              <StatSection title="Does the signal carry information?">
                <StatCard
                  label="Mean RankIC"
                  value={fmtNumber(data.ic.summary.mean_rank_ic, 4)}
                  caption="out-of-sample only"
                />
                <StatCard
                  label="ICIR"
                  value={fmtNumber(data.ic.summary.icir)}
                  caption="mean IC / std IC"
                />
                <StatCard
                  label="Positive IC ratio"
                  value={fmtPct(data.ic.summary.positive_ic_ratio)}
                  caption={`of ${data.ic.summary.n_periods} periods`}
                />
              </StatSection>

              <StatSection title="Does it survive costs?">
                <StatCard
                  label="Q5 − Q1 gross"
                  value={fmtPct(data.long_short.cumulative_final)}
                  caption="before transaction costs"
                />
                <StatCard
                  label="Q5 − Q1 net"
                  value={fmtPct(data.long_short.cumulative_final_net_of_cost)}
                  caption="after transaction costs"
                />
                <StatCard
                  label="Turnover"
                  value={fmtNumber(data.quantiles.turnover.mean)}
                  caption="cost pressure per rebalance"
                />
              </StatSection>

              <StatSection title="Is it alpha or beta?">
                <StatCard
                  label="Net alpha"
                  value={fmtPct(regression?.alpha_annualized)}
                  caption={`95% CI ${fmtPct(regression?.alpha_annualized_ci_low)} to ${fmtPct(regression?.alpha_annualized_ci_high)}`}
                />
                <StatCard
                  label="Alpha t-stat"
                  value={fmtNumber(regression?.t_stat_alpha)}
                  caption={`n = ${regression?.n_observations ?? 0} periods`}
                />
                <StatCard
                  label="Market beta"
                  value={fmtNumber(regression?.beta)}
                  caption={`vs ${data.capm.benchmark_symbol}`}
                />
                <StatCard
                  label="R²"
                  value={fmtNumber(regression?.r_squared)}
                  caption="variance explained by beta"
                />
              </StatSection>

              <StatSection title="Stable enough to trust?">
                <StatCard
                  label="Sharpe (net)"
                  value={fmtNumber(data.portfolio_risk.sharpe_ratio_net)}
                  caption="annualized, long-short book"
                />
                <StatCard
                  label="Max drawdown (net)"
                  value={fmtPct(data.portfolio_risk.max_drawdown_net)}
                  caption="peak to trough"
                />
              </StatSection>

              <p className="alpha-lab__provenance-note">
                Source: factor_validation service · {data.universe_id} vs{" "}
                {data.capm.benchmark_symbol} · {data.provenance.start_date} →{" "}
                {data.provenance.end_date ?? "latest"}
              </p>

              <div className="alpha-lab__chart-panel">
                <p className="alpha-lab__chart-title">
                  Where did performance come from?
                </p>
                <p className="alpha-lab__chart-subtitle">
                  Long-short portfolio return decomposed into beta contribution,
                  residual alpha, and cost drag
                </p>
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
                        name="Cost drag"
                        fill="var(--chart-series-3)"
                        stroke="var(--chart-series-3)"
                        fillOpacity={0.18}
                        strokeWidth={1}
                      />
                      <Line
                        type="monotone"
                        dataKey="betaContribution"
                        name="Beta contribution"
                        stroke="var(--chart-series-2)"
                        strokeDasharray="5 4"
                        dot={false}
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="residualAlpha"
                        name="Residual alpha"
                        stroke="var(--chart-series-1)"
                        dot={false}
                        strokeWidth={2.5}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                <p className="alpha-lab__methodology">
                  {decomposition?.methodology}
                </p>
              </div>
            </>
          ) : null}

          {tab === "question" ? (
            <div className="alpha-lab__panel">
              <h3>Why this question</h3>
              <p className="alpha-lab__lede">
                Individual investors can generate signals faster than they can
                validate them. This page exists to slow that down, on purpose.
              </p>
              <ol className="alpha-lab__findings">
                <li>
                  <strong>No repeatable research process.</strong> The
                  question, success criteria, and benchmark are fixed above
                  before any result is shown — universe, rebalance frequency,
                  and forward window are stated, not chosen after the fact.
                </li>
                <li>
                  <strong>Outperformance isn&rsquo;t automatically alpha.</strong>{" "}
                  The stats below regress this factor&rsquo;s returns against
                  a market benchmark to separate residual alpha from beta
                  exposure — see Market beta and the decomposition chart on
                  the Alpha Validation tab.
                </li>
                <li>
                  <strong>Evidence decays after publication.</strong> Rolling
                  IC/alpha-decay monitoring is not built yet — the
                  Attribution &amp; Monitor tab says so honestly rather than
                  faking a chart.
                </li>
              </ol>
              <p>
                Current decision: <strong>{decision.label}</strong> — derived
                directly from the factor benchmark verdict (
                <code>{String(verdict ?? "unavailable")}</code>), not a
                separately fabricated judgment.
              </p>
              <p className="alpha-lab__scope-note">
                Scope: this system validates cross-sectional factor and
                portfolio evidence. It does not generate single-stock
                buy/sell signals — any per-symbol membership shown elsewhere
                is transparency, not a recommendation.
              </p>
            </div>
          ) : null}

          {tab === "data" ? (
            <div className="alpha-lab__panel">
              <h3>Data & signals</h3>
              <dl className="alpha-lab__kv">
                <dt>Universe</dt>
                <dd>
                  {data.universe_id} ({data.provenance.symbols_used.length} symbols
                  used of {data.provenance.universe_symbols.length})
                </dd>
                <dt>Date range</dt>
                <dd>
                  {data.provenance.start_date} → {data.provenance.end_date ?? "latest"}
                </dd>
                <dt>Factor periods</dt>
                <dd>{data.provenance.n_factor_periods}</dd>
                <dt>Benchmark</dt>
                <dd>{data.provenance.benchmark_symbol}</dd>
              </dl>
              {data.warnings.length > 0 ? (
                <>
                  <h4>Warnings</h4>
                  <ul className="alpha-lab__warnings">
                    {data.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="alpha-lab__muted">No data-quality warnings for this run.</p>
              )}
            </div>
          ) : null}

          {tab === "portfolio" ? (
            <NotYetBuiltPanel
              title="Portfolio & beta — not yet built"
              note="Sector and style neutralization at the portfolio level maps to this
              repo's own not-yet-started Phase 5.2 (Portfolio Exposure Snapshots). The
              Alpha Validation tab already shows a real single-factor market-beta
              regression on the long-short portfolio; this tab will extend that to
              multi-member portfolios with sector/style exposure once that phase lands."
            />
          ) : null}

          {tab === "attribution" ? (
            <NotYetBuiltPanel
              title="Attribution & monitor — not yet built"
              note="Rolling IC/alpha-decay monitoring and portfolio-level alpha/beta/sector
              attribution do not exist yet in this codebase — the post-trade module
              computes execution/cost attribution (fees, slippage, venue), a related
              but distinct question. This tab is reserved for that future slice."
            />
          ) : null}
        </>
      ) : null}

      {status === "ready" ? (
        <p className="alpha-lab__pipeline-recap">
          Question → Data → Alpha Validation → Portfolio &amp; Beta (planned) →
          Attribution &amp; Monitor (planned) → Decision:{" "}
          <strong>{decision.label}</strong>
        </p>
      ) : null}
    </div>
  );
}
