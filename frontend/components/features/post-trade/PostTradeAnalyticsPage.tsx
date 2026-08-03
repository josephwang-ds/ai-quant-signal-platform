"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import AppShell from "@/components/layout/AppShell";
import { getLocalizedApiDisplayMessage } from "@/lib/apiRequest";
import {
  DEMO_ATTRIBUTION_REQUEST,
  fetchAnomalyDetection,
  fetchPerformanceAttribution,
} from "@/lib/postTradeAnalytics";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type {
  AnomalyDetectionResult,
  AttributionResult,
  ScoredMetricPoint,
} from "@/types/postTradeAnalytics";

type LoadState = "loading" | "ready" | "error";
type GroupBy = "venue" | "strategy";

const COPY = {
  en: {
    eyebrow: "Research utility / Post-trade",
    title: "Post-Trade Analytics",
    lede: "Execution quality and infrastructure diagnostics",
    dataset: "Dataset",
    datasetValue: "Synthetic · deterministic",
    scope: "Scope",
    scopeValue: "6 fills · 2 gateways",
    window: "Window",
    windowValue: "09:30–09:47 UTC",
    disclosure:
      "Demonstration fixture — not live orders, exchange data, or realized investment performance.",
    performanceNav: "Performance",
    infrastructureNav: "Infrastructure",
    attributionTitle: "Performance Attribution",
    attributionIntro:
      "Active PnL reconciled against benchmark, explicit fees, and realized slippage.",
    detectorTitle: "Latency Degradation",
    detectorIntro:
      "Past-only robust baseline with a complete scoring trace for every gateway.",
    loading: "Calculating post-trade evidence…",
    retry: "Retry",
    unavailable: "Post-trade evidence could not be calculated.",
    observations: "Observations",
    notional: "Notional",
    grossEdge: "Gross edge",
    netActive: "Net active",
    totalDrag: "Execution drag",
    reconciliation: "Reconciliation",
    decomposition: "PnL bridge",
    breakdown: "Contribution by",
    venue: "Venue",
    strategy: "Strategy",
    rank: "Rank",
    fees: "Fees",
    slippage: "Slippage",
    netPnl: "Net active PnL",
    contributionUsd: "Contribution (USD)",
    monitoring: "Latency monitor",
    gateway: "Gateway",
    baseline: "Rolling median",
    threshold: "Alert threshold",
    observed: "Observed",
    detector: "Detector",
    detectorValue: "Rolling median / MAD",
    history: "Baseline window",
    historyValue: "12 prior observations",
    direction: "Direction",
    directionValue: "High-side degradation",
    leakage: "Leakage guard",
    leakageValue: "Past observations only",
    scored: "Scored",
    incidents: "Incidents",
    latest: "Latest",
    eventLog: "Exception log",
    time: "Time",
    metricEntity: "Metric / entity",
    robustZ: "Robust z",
    severity: "State",
    noAnomalies: "No threshold crossings.",
    methodology: "Method and data contract",
    warmup: "Warm-up samples are displayed but not scored.",
  },
  zh: {
    eyebrow: "研究工具 / 交易后分析",
    title: "交易后分析",
    lede: "执行质量与基础设施性能诊断",
    dataset: "数据集",
    datasetValue: "合成样例 · 确定性",
    scope: "范围",
    scopeValue: "6 笔成交 · 2 个网关",
    window: "窗口",
    windowValue: "09:30–09:47 UTC",
    disclosure: "演示样例——不代表真实订单、交易所数据或已实现投资业绩。",
    performanceNav: "业绩",
    infrastructureNav: "基础设施",
    attributionTitle: "业绩归因",
    attributionIntro: "将主动收益与基准、显式费用和实际滑点逐项对账。",
    detectorTitle: "延迟退化",
    detectorIntro: "仅使用历史观测建立稳健基线，并保留每个网关的完整评分轨迹。",
    loading: "正在计算交易后证据…",
    retry: "重试",
    unavailable: "无法计算交易后分析证据。",
    observations: "观测数",
    notional: "名义金额",
    grossEdge: "毛收益优势",
    netActive: "净主动收益",
    totalDrag: "执行拖累",
    reconciliation: "对账误差",
    decomposition: "PnL 桥接",
    breakdown: "贡献拆解维度",
    venue: "交易场所",
    strategy: "策略",
    rank: "排名",
    fees: "费用",
    slippage: "滑点",
    netPnl: "净主动收益",
    contributionUsd: "贡献（USD）",
    monitoring: "延迟监控",
    gateway: "网关",
    baseline: "滚动中位数",
    threshold: "告警阈值",
    observed: "观测值",
    detector: "检测器",
    detectorValue: "滚动中位数 / MAD",
    history: "基线窗口",
    historyValue: "前 12 个观测",
    direction: "检测方向",
    directionValue: "高侧退化",
    leakage: "防泄漏",
    leakageValue: "仅历史观测",
    scored: "已评分",
    incidents: "异常事件",
    latest: "最新值",
    eventLog: "异常日志",
    time: "时间",
    metricEntity: "指标 / 实体",
    robustZ: "稳健 z",
    severity: "状态",
    noAnomalies: "没有阈值越界。",
    methodology: "方法与数据契约",
    warmup: "预热样本会展示，但不参与评分。",
  },
} as const;

function formatUsd(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatBps(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)} bps`;
}

function formatMs(value: number): string {
  return `${value.toFixed(2)} ms`;
}

function shortTime(timestamp: string): string {
  return new Date(timestamp).toISOString().slice(11, 16);
}

function chartRows(points: ScoredMetricPoint[], entity: string) {
  return points
    .filter((point) => point.entity === entity)
    .map((point) => ({
      time: shortTime(point.timestamp),
      value: point.value,
      baseline: point.baseline_median,
      threshold: point.upper_threshold,
      incident:
        point.status === "warning" || point.status === "critical"
          ? point.value
          : null,
    }));
}

export default function PostTradeAnalyticsPage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const copy = COPY[language];
  const [state, setState] = useState<LoadState>("loading");
  const [groupBy, setGroupBy] = useState<GroupBy>("venue");
  const [selectedEntity, setSelectedEntity] = useState("gateway-a");
  const [retryKey, setRetryKey] = useState(0);
  const [attribution, setAttribution] = useState<AttributionResult | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyDetectionResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const run = async () => {
      setState("loading");
      setError("");
      try {
        const [attributionResult, anomalyResult] = await Promise.all([
          fetchPerformanceAttribution(
            { ...DEMO_ATTRIBUTION_REQUEST, group_by: groupBy },
            controller.signal
          ),
          fetchAnomalyDetection(undefined, controller.signal),
        ]);
        if (!active) return;
        setAttribution(attributionResult);
        setAnomalies(anomalyResult);
        setState("ready");
      } catch (caught) {
        if (!active || controller.signal.aborted) return;
        setError(
          getLocalizedApiDisplayMessage(caught, language, copy.unavailable)
        );
        setState("error");
      }
    };
    void run();
    return () => {
      active = false;
      controller.abort();
    };
  }, [copy.unavailable, groupBy, language, retryKey]);

  const entities = useMemo(
    () => Array.from(new Set(anomalies?.points.map((point) => point.entity) ?? [])),
    [anomalies]
  );
  const selectedPoints = useMemo(
    () => chartRows(anomalies?.points ?? [], selectedEntity),
    [anomalies, selectedEntity]
  );
  const selectedSeries = anomalies?.series.find(
    (item) => item.entity === selectedEntity
  );
  const totalDragBps = attribution
    ? attribution.fee_drag_bps + attribution.slippage_drag_bps
    : 0;

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="post-trade" data-testid="post-trade-analytics">
        <header className="post-trade__header">
          <div className="post-trade__heading">
            <p className="post-trade__eyebrow">{copy.eyebrow}</p>
            <h1>{copy.title}</h1>
            <p>{copy.lede}</p>
          </div>
          <dl className="post-trade__scope">
            <div>
              <dt>{copy.dataset}</dt>
              <dd>{copy.datasetValue}</dd>
            </div>
            <div>
              <dt>{copy.scope}</dt>
              <dd>{copy.scopeValue}</dd>
            </div>
            <div>
              <dt>{copy.window}</dt>
              <dd>{copy.windowValue}</dd>
            </div>
          </dl>
          <p className="post-trade__disclosure" role="note">
            {copy.disclosure}
          </p>
          <nav className="post-trade__local-nav" aria-label={copy.title}>
            <a href="#performance-attribution">{copy.performanceNav}</a>
            <a href="#latency-degradation">{copy.infrastructureNav}</a>
          </nav>
        </header>

        {state === "loading" ? (
          <section className="post-trade__state" role="status">
            <span className="post-trade__loading-dot" aria-hidden="true" />
            {copy.loading}
          </section>
        ) : null}

        {state === "error" ? (
          <section className="post-trade__state post-trade__state--error" role="alert">
            <p>{error || copy.unavailable}</p>
            <button
              type="button"
              className="btn"
              onClick={() => setRetryKey((value) => value + 1)}
            >
              {copy.retry}
            </button>
          </section>
        ) : null}

        {state === "ready" && attribution && anomalies ? (
          <>
            <section
              id="performance-attribution"
              className="post-trade__module"
              aria-labelledby="performance-attribution-title"
              data-testid="performance-attribution"
            >
              <header className="post-trade__module-header">
                <div>
                  <p className="post-trade__section-code">PTA / 01</p>
                  <h2 id="performance-attribution-title">{copy.attributionTitle}</h2>
                  <p>{copy.attributionIntro}</p>
                </div>
                <div className="post-trade__segmented" aria-label={copy.breakdown}>
                  {(["venue", "strategy"] as const).map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={groupBy === value ? "is-active" : ""}
                      aria-pressed={groupBy === value}
                      onClick={() => setGroupBy(value)}
                    >
                      {value === "venue" ? copy.venue : copy.strategy}
                    </button>
                  ))}
                </div>
              </header>

              <dl className="post-trade__metrics">
                <div>
                  <dt>{copy.notional}</dt>
                  <dd>{formatUsd(attribution.total_notional_usd)}</dd>
                  <small>{attribution.observation_count} {copy.observations.toLowerCase()}</small>
                </div>
                <div>
                  <dt>{copy.grossEdge}</dt>
                  <dd className="is-positive">{formatBps(attribution.gross_edge_bps)}</dd>
                  <small>{formatUsd(attribution.components[0].contribution_usd)}</small>
                </div>
                <div>
                  <dt>{copy.totalDrag}</dt>
                  <dd className="is-negative">{formatBps(totalDragBps)}</dd>
                  <small>
                    {copy.fees} {formatBps(attribution.fee_drag_bps)} · {copy.slippage}{" "}
                    {formatBps(attribution.slippage_drag_bps)}
                  </small>
                </div>
                <div>
                  <dt>{copy.netActive}</dt>
                  <dd className={attribution.net_active_bps >= 0 ? "is-positive" : "is-negative"}>
                    {formatBps(attribution.net_active_bps)}
                  </dd>
                  <small>{formatUsd(attribution.net_active_usd)}</small>
                </div>
              </dl>

              <div className="post-trade__attribution-grid">
                <article className="post-trade__panel">
                  <header>
                    <h3>{copy.decomposition}</h3>
                    <span>
                      {copy.reconciliation}: {formatUsd(attribution.reconciliation_error_usd)}
                    </span>
                  </header>
                  <div className="post-trade__bridge" role="img" aria-label={copy.decomposition}>
                    {attribution.components.map((component, index) => (
                      <div
                        key={component.key}
                        className={`post-trade__bridge-step ${
                          component.contribution_bps >= 0 ? "is-positive" : "is-negative"
                        }${component.key === "net_active" ? " is-total" : ""}`}
                      >
                        <span>{String(index + 1).padStart(2, "0")}</span>
                        <div>
                          <strong>{component.label}</strong>
                          <small>{formatUsd(component.contribution_usd)}</small>
                        </div>
                        <b>{formatBps(component.contribution_bps)}</b>
                      </div>
                    ))}
                  </div>
                </article>

                <article className="post-trade__panel">
                  <header>
                    <h3>
                      {copy.breakdown} {groupBy === "venue" ? copy.venue : copy.strategy}
                    </h3>
                    <span>{copy.netPnl}</span>
                  </header>
                  <ol className="post-trade__ranking">
                    {attribution.groups.map((group, index) => (
                      <li key={group.group}>
                        <span>{String(index + 1).padStart(2, "0")}</span>
                        <div>
                          <strong>{group.group}</strong>
                          <small>{formatUsd(group.notional_usd)}</small>
                        </div>
                        <b className={group.net_active_bps >= 0 ? "is-positive" : "is-negative"}>
                          {formatBps(group.net_active_bps)}
                        </b>
                      </li>
                    ))}
                  </ol>
                </article>
              </div>

              <div className="post-trade__table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{copy.rank}</th>
                      <th>{groupBy === "venue" ? copy.venue : copy.strategy}</th>
                      <th>{copy.notional}</th>
                      <th>{copy.grossEdge}</th>
                      <th>{copy.fees}</th>
                      <th>{copy.slippage}</th>
                      <th>{copy.netPnl}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attribution.groups.map((group, index) => (
                      <tr key={group.group}>
                        <td>{String(index + 1).padStart(2, "0")}</td>
                        <th>{group.group}</th>
                        <td>{formatUsd(group.notional_usd)}</td>
                        <td>{formatBps(group.gross_edge_bps)}</td>
                        <td>{formatBps(group.fee_drag_bps)}</td>
                        <td>{formatBps(group.slippage_drag_bps)}</td>
                        <td>{formatBps(group.net_active_bps)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <details className="post-trade__method">
                <summary>{copy.methodology}</summary>
                <p>{attribution.methodology}</p>
              </details>
            </section>

            <section
              id="latency-degradation"
              className="post-trade__module"
              aria-labelledby="latency-degradation-title"
              data-testid="anomaly-detection"
            >
              <header className="post-trade__module-header">
                <div>
                  <p className="post-trade__section-code">PTA / 02</p>
                  <h2 id="latency-degradation-title">{copy.detectorTitle}</h2>
                  <p>{copy.detectorIntro}</p>
                </div>
                <div className="post-trade__segmented" aria-label={copy.gateway}>
                  {entities.map((entity) => (
                    <button
                      key={entity}
                      type="button"
                      className={selectedEntity === entity ? "is-active" : ""}
                      aria-pressed={selectedEntity === entity}
                      onClick={() => setSelectedEntity(entity)}
                    >
                      {entity}
                    </button>
                  ))}
                </div>
              </header>

              <dl className="post-trade__metrics post-trade__metrics--monitoring">
                <div>
                  <dt>{copy.latest}</dt>
                  <dd>{formatMs(selectedSeries?.latest_value ?? 0)}</dd>
                  <small>{selectedEntity}</small>
                </div>
                <div>
                  <dt>{copy.baseline}</dt>
                  <dd>{formatMs(selectedSeries?.latest_baseline_median ?? 0)}</dd>
                  <small>{copy.historyValue}</small>
                </div>
                <div>
                  <dt>{copy.scored}</dt>
                  <dd>{selectedSeries?.scored_count ?? 0}</dd>
                  <small>{anomalies.observation_count} {copy.observations.toLowerCase()}</small>
                </div>
                <div>
                  <dt>{copy.incidents}</dt>
                  <dd className={selectedSeries?.anomaly_count ? "is-negative" : "is-positive"}>
                    {selectedSeries?.anomaly_count ?? 0}
                  </dd>
                  <small>{selectedSeries?.status ?? "normal"}</small>
                </div>
              </dl>

              <div className="post-trade__monitor-grid">
                <article className="post-trade__panel post-trade__chart-panel">
                  <header>
                    <h3>{copy.monitoring}</h3>
                    <span>ack_latency_ms · {selectedEntity}</span>
                  </header>
                  <div className="post-trade__chart" data-testid="latency-chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart
                        data={selectedPoints}
                        margin={{ top: 14, right: 12, bottom: 0, left: -18 }}
                      >
                        <CartesianGrid stroke="var(--border-subtle)" vertical={false} />
                        <XAxis
                          dataKey="time"
                          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                          axisLine={{ stroke: "var(--border-subtle)" }}
                          tickLine={false}
                        />
                        <YAxis
                          unit=" ms"
                          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          domain={["auto", "auto"]}
                        />
                        <Tooltip
                          contentStyle={{
                            background: "var(--surface)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: 0,
                          }}
                          labelStyle={{ color: "var(--text-primary)" }}
                          itemStyle={{ color: "var(--text-secondary)" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="threshold"
                          name={copy.threshold}
                          stroke="var(--danger, #a53b36)"
                          strokeDasharray="4 4"
                          strokeWidth={1}
                          dot={false}
                          connectNulls
                        />
                        <Line
                          type="monotone"
                          dataKey="baseline"
                          name={copy.baseline}
                          stroke="var(--text-muted)"
                          strokeDasharray="2 3"
                          strokeWidth={1}
                          dot={false}
                          connectNulls
                        />
                        <Line
                          type="linear"
                          dataKey="value"
                          name={copy.observed}
                          stroke="var(--accent, #4d8ee8)"
                          strokeWidth={2}
                          dot={{ r: 2, fill: "var(--accent, #4d8ee8)" }}
                        />
                        <Scatter
                          dataKey="incident"
                          name={copy.incidents}
                          fill="var(--danger, #d65f5f)"
                        />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="post-trade__chart-note">{copy.warmup}</p>
                </article>

                <aside className="post-trade__panel post-trade__detector-config">
                  <header>
                    <h3>{copy.detector}</h3>
                    <span>robust_z / v1</span>
                  </header>
                  <dl>
                    <div>
                      <dt>{copy.detector}</dt>
                      <dd>{copy.detectorValue}</dd>
                    </div>
                    <div>
                      <dt>{copy.history}</dt>
                      <dd>{copy.historyValue}</dd>
                    </div>
                    <div>
                      <dt>{copy.threshold}</dt>
                      <dd>{anomalies.threshold.toFixed(1)} robust z</dd>
                    </div>
                    <div>
                      <dt>{copy.direction}</dt>
                      <dd>{copy.directionValue}</dd>
                    </div>
                    <div>
                      <dt>{copy.leakage}</dt>
                      <dd>{copy.leakageValue}</dd>
                    </div>
                  </dl>
                </aside>
              </div>

              <article className="post-trade__panel">
                <header>
                  <h3>{copy.eventLog}</h3>
                  <span>{anomalies.anomaly_count} / {anomalies.scored_count}</span>
                </header>
                {anomalies.anomalies.length ? (
                  <div className="post-trade__table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>{copy.time}</th>
                          <th>{copy.metricEntity}</th>
                          <th>{copy.observed}</th>
                          <th>{copy.baseline}</th>
                          <th>{copy.robustZ}</th>
                          <th>{copy.severity}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {anomalies.anomalies.map((event) => (
                          <tr key={`${event.timestamp}-${event.metric}-${event.entity}`}>
                            <td>{shortTime(event.timestamp)}</td>
                            <th>
                              {event.metric}
                              <small>{event.entity}</small>
                            </th>
                            <td>{formatMs(event.value)}</td>
                            <td>{formatMs(event.baseline_median)}</td>
                            <td>{event.robust_z_score.toFixed(2)}</td>
                            <td>
                              <span className={`post-trade__severity is-${event.severity}`}>
                                {event.severity}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p>{copy.noAnomalies}</p>
                )}
              </article>

              <details className="post-trade__method">
                <summary>{copy.methodology}</summary>
                <p>{anomalies.methodology}</p>
              </details>
            </section>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
