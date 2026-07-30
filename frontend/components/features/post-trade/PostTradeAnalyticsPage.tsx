"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  fetchAnomalyDetection,
  fetchPerformanceAttribution,
} from "@/lib/postTradeAnalytics";
import {
  getLocalizedApiDisplayMessage,
} from "@/lib/apiRequest";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type {
  AnomalyDetectionResult,
  AttributionResult,
} from "@/types/postTradeAnalytics";

type LoadState = "loading" | "ready" | "error";

const COPY = {
  en: {
    eyebrow: "Post-Trade Analytics",
    title: "From trading activity to measurable decisions",
    lede:
      "A deterministic analysis layer for explaining performance and detecting infrastructure degradation. Built for research demonstration with transparent methodology.",
    disclosureTitle: "Data boundary",
    disclosure:
      "Results below use a labeled deterministic synthetic fixture. They demonstrate the analytical contract and do not represent live orders, exchange data, or investment performance.",
    attributionTitle: "Performance Attribution",
    attributionIntro:
      "Reconcile active PnL into gross edge versus benchmark, fees, and realized slippage. Every total is notional-weighted and reconciles in USD.",
    anomalyTitle: "Anomaly Detection",
    anomalyIntro:
      "Detect latency degradation with a past-only rolling median/MAD baseline. Future observations never enter the current baseline.",
    loading: "Calculating deterministic evidence…",
    retry: "Retry analysis",
    unavailable: "Post-trade evidence could not be calculated.",
    observations: "Observations",
    notional: "Notional analyzed",
    netActive: "Net active PnL",
    reconciliation: "Reconciliation error",
    decomposition: "Attribution decomposition",
    venueBreakdown: "Venue breakdown",
    venue: "Venue",
    grossEdge: "Gross edge",
    fees: "Fees",
    slippage: "Slippage",
    scored: "Scored observations",
    anomalies: "Anomalies detected",
    threshold: "Robust z threshold",
    events: "Detected degradation events",
    time: "Time (UTC)",
    metric: "Metric / entity",
    value: "Observed",
    baseline: "Baseline median",
    robustZ: "Robust z",
    severity: "Severity",
    noAnomalies: "No degradation events crossed the configured threshold.",
    methodology: "Methodology",
  },
  zh: {
    eyebrow: "交易后分析",
    title: "将交易活动转化为可量化决策",
    lede:
      "用确定性分析解释业绩来源，并识别基础设施性能退化。方法透明、结果可复核，面向研究演示。",
    disclosureTitle: "数据边界",
    disclosure:
      "以下结果使用明确标注的确定性合成样例，仅用于展示分析契约，不代表真实订单、交易所数据或投资业绩。",
    attributionTitle: "业绩归因",
    attributionIntro:
      "将相对基准的主动收益拆解为毛收益优势、费用与实际滑点。所有结果按名义金额加权，并以美元严格对账。",
    anomalyTitle: "异常检测",
    anomalyIntro:
      "使用只包含历史数据的滚动中位数/MAD 基线检测延迟退化，当前基线绝不读取未来观测。",
    loading: "正在计算确定性证据…",
    retry: "重新运行",
    unavailable: "无法计算交易后分析证据。",
    observations: "观测数",
    notional: "分析名义金额",
    netActive: "净主动收益",
    reconciliation: "对账误差",
    decomposition: "归因拆解",
    venueBreakdown: "交易场所拆解",
    venue: "交易场所",
    grossEdge: "毛收益优势",
    fees: "费用",
    slippage: "滑点",
    scored: "已评分观测",
    anomalies: "检出异常",
    threshold: "稳健 z 阈值",
    events: "性能退化事件",
    time: "时间（UTC）",
    metric: "指标 / 实体",
    value: "观测值",
    baseline: "基线中位数",
    robustZ: "稳健 z",
    severity: "严重度",
    noAnomalies: "没有观测越过当前检测阈值。",
    methodology: "方法",
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

export default function PostTradeAnalyticsPage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const copy = COPY[language];
  const [state, setState] = useState<LoadState>("loading");
  const [attribution, setAttribution] = useState<AttributionResult | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyDetectionResult | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setState("loading");
    setError("");
    const controller = new AbortController();
    try {
      const [attributionResult, anomalyResult] = await Promise.all([
        fetchPerformanceAttribution(undefined, controller.signal),
        fetchAnomalyDetection(undefined, controller.signal),
      ]);
      setAttribution(attributionResult);
      setAnomalies(anomalyResult);
      setState("ready");
    } catch (caught) {
      setError(
        getLocalizedApiDisplayMessage(caught, language, copy.unavailable)
      );
      setState("error");
    }
    return () => controller.abort();
  }, [copy.unavailable, language]);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const run = async () => {
      setState("loading");
      try {
        const [attributionResult, anomalyResult] = await Promise.all([
          fetchPerformanceAttribution(undefined, controller.signal),
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
  }, [copy.unavailable, language]);

  const maxComponent = useMemo(
    () =>
      Math.max(
        1,
        ...(attribution?.components.map((item) =>
          Math.abs(item.contribution_bps)
        ) ?? [])
      ),
    [attribution]
  );

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="post-trade" data-testid="post-trade-analytics">
        <header className="post-trade__hero">
          <p className="post-trade__eyebrow">{copy.eyebrow}</p>
          <h1>{copy.title}</h1>
          <p>{copy.lede}</p>
          <aside className="post-trade__disclosure" role="note">
            <strong>{copy.disclosureTitle}</strong>
            <span>{copy.disclosure}</span>
          </aside>
        </header>

        {state === "loading" ? (
          <section className="post-trade__state" role="status">
            {copy.loading}
          </section>
        ) : null}

        {state === "error" ? (
          <section className="post-trade__state post-trade__state--error" role="alert">
            <p>{error || copy.unavailable}</p>
            <button type="button" className="btn" onClick={() => void load()}>
              {copy.retry}
            </button>
          </section>
        ) : null}

        {state === "ready" && attribution && anomalies ? (
          <>
            <section
              className="post-trade__module"
              aria-labelledby="performance-attribution-title"
              data-testid="performance-attribution"
            >
              <header>
                <p className="post-trade__module-number">01</p>
                <div>
                  <h2 id="performance-attribution-title">{copy.attributionTitle}</h2>
                  <p>{copy.attributionIntro}</p>
                </div>
              </header>

              <dl className="post-trade__metrics">
                <div>
                  <dt>{copy.observations}</dt>
                  <dd>{attribution.observation_count}</dd>
                </div>
                <div>
                  <dt>{copy.notional}</dt>
                  <dd>{formatUsd(attribution.total_notional_usd)}</dd>
                </div>
                <div>
                  <dt>{copy.netActive}</dt>
                  <dd className={attribution.net_active_bps >= 0 ? "is-positive" : "is-negative"}>
                    {formatBps(attribution.net_active_bps)}
                  </dd>
                </div>
                <div>
                  <dt>{copy.reconciliation}</dt>
                  <dd>{formatUsd(attribution.reconciliation_error_usd)}</dd>
                </div>
              </dl>

              <div className="post-trade__panel">
                <h3>{copy.decomposition}</h3>
                <ul className="post-trade__bars">
                  {attribution.components.map((component) => (
                    <li key={component.key}>
                      <span>{component.label}</span>
                      <div>
                        <i
                          className={
                            component.contribution_bps >= 0
                              ? "is-positive"
                              : "is-negative"
                          }
                          style={{
                            width: `${Math.max(
                              4,
                              (Math.abs(component.contribution_bps) / maxComponent) *
                                100
                            )}%`,
                          }}
                        />
                      </div>
                      <strong>{formatBps(component.contribution_bps)}</strong>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="post-trade__panel">
                <h3>{copy.venueBreakdown}</h3>
                <div className="post-trade__table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>{copy.venue}</th>
                        <th>{copy.notional}</th>
                        <th>{copy.grossEdge}</th>
                        <th>{copy.fees}</th>
                        <th>{copy.slippage}</th>
                        <th>{copy.netActive}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attribution.groups.map((group) => (
                        <tr key={group.group}>
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
              </div>

              <details className="post-trade__method">
                <summary>{copy.methodology}</summary>
                <p>{attribution.methodology}</p>
              </details>
            </section>

            <section
              className="post-trade__module"
              aria-labelledby="anomaly-detection-title"
              data-testid="anomaly-detection"
            >
              <header>
                <p className="post-trade__module-number">02</p>
                <div>
                  <h2 id="anomaly-detection-title">{copy.anomalyTitle}</h2>
                  <p>{copy.anomalyIntro}</p>
                </div>
              </header>

              <dl className="post-trade__metrics">
                <div>
                  <dt>{copy.observations}</dt>
                  <dd>{anomalies.observation_count}</dd>
                </div>
                <div>
                  <dt>{copy.scored}</dt>
                  <dd>{anomalies.scored_count}</dd>
                </div>
                <div>
                  <dt>{copy.anomalies}</dt>
                  <dd className={anomalies.anomaly_count ? "is-negative" : "is-positive"}>
                    {anomalies.anomaly_count}
                  </dd>
                </div>
                <div>
                  <dt>{copy.threshold}</dt>
                  <dd>{anomalies.threshold.toFixed(1)}</dd>
                </div>
              </dl>

              <div className="post-trade__panel">
                <h3>{copy.events}</h3>
                {anomalies.anomalies.length ? (
                  <div className="post-trade__table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>{copy.time}</th>
                          <th>{copy.metric}</th>
                          <th>{copy.value}</th>
                          <th>{copy.baseline}</th>
                          <th>{copy.robustZ}</th>
                          <th>{copy.severity}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {anomalies.anomalies.map((event) => (
                          <tr key={`${event.timestamp}-${event.metric}-${event.entity}`}>
                            <td>{new Date(event.timestamp).toISOString().slice(11, 16)}</td>
                            <th>
                              {event.metric}
                              <small>{event.entity}</small>
                            </th>
                            <td>{event.value.toFixed(2)} ms</td>
                            <td>{event.baseline_median.toFixed(2)} ms</td>
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
              </div>

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
