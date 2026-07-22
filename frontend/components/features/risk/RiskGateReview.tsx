"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import { runRiskReview, type RiskReviewResponse } from "@/lib/api";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import {
  translateAllowedAction,
  translateRiskLabel,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { BacktestStrategy, CombinedMode } from "@/types/market";

const DEFAULT_TICKER = "AAPL";
const DEFAULT_START_DATE = "2022-01-01";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.001;

const COMPONENT_ORDER = [
  "drawdown",
  "volatility",
  "sharpe_decline",
  "cost_drag",
  "consecutive_losses",
  "single_trade_loss",
  "signal_conflict",
] as const;

type ComponentKey = (typeof COMPONENT_ORDER)[number];

const COMPONENT_LABEL_KEYS: Record<ComponentKey, "riskComponentDrawdown" | "riskComponentVolatility" | "riskComponentSharpeDecline" | "riskComponentCostDrag" | "riskComponentConsecutiveLosses" | "riskComponentSingleTradeLoss" | "riskComponentSignalConflict"> = {
  drawdown: "riskComponentDrawdown",
  volatility: "riskComponentVolatility",
  sharpe_decline: "riskComponentSharpeDecline",
  cost_drag: "riskComponentCostDrag",
  consecutive_losses: "riskComponentConsecutiveLosses",
  single_trade_loss: "riskComponentSingleTradeLoss",
  signal_conflict: "riskComponentSignalConflict",
};

/**
 * Risk Review：参数表单 → POST /api/v1/risk/review → 渲染五档评估。
 * 指标与等级均来自后端；前端不计算、不编造。
 */
export default function RiskGateReview() {
  const { language, tr } = useWorkspaceLanguage();
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [startDate, setStartDate] = useState(DEFAULT_START_DATE);
  const [endDate, setEndDate] = useState("");
  const [strategy, setStrategy] = useState<BacktestStrategy>("ma_crossover");
  const [shortWindow, setShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [longWindow, setLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [momentumWindow, setMomentumWindow] = useState(DEFAULT_MOMENTUM_WINDOW);
  const [combinedMode, setCombinedMode] = useState<CombinedMode>("conservative");
  const [transactionCost, setTransactionCost] = useState(
    String(DEFAULT_TRANSACTION_COST)
  );
  const [result, setResult] = useState<RiskReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    const normalizedTicker = ticker.trim().toUpperCase();
    const parsedShortWindow = Number(shortWindow);
    const parsedLongWindow = Number(longWindow);
    const parsedMomentumWindow = Number(momentumWindow);
    const parsedTransactionCost = Number(transactionCost);

    if (!normalizedTicker) {
      setError(tr("tickerEmpty"));
      return;
    }

    if (
      (strategy === "ma_crossover" || strategy === "combined_signal") &&
      (!Number.isFinite(parsedShortWindow) ||
        !Number.isFinite(parsedLongWindow) ||
        parsedShortWindow >= parsedLongWindow)
    ) {
      setError(tr("shortLessThanLong"));
      return;
    }

    if (
      (strategy === "momentum" || strategy === "combined_signal") &&
      (!Number.isFinite(parsedMomentumWindow) ||
        parsedMomentumWindow < 5 ||
        parsedMomentumWindow > 252)
    ) {
      setError(tr("momentumRange"));
      return;
    }

    if (!Number.isFinite(parsedTransactionCost) || parsedTransactionCost < 0) {
      setError(tr("transactionCostInvalid"));
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await runRiskReview({
        ticker: normalizedTicker,
        start_date: startDate,
        end_date: endDate || undefined,
        strategy,
        short_window: parsedShortWindow,
        long_window: parsedLongWindow,
        momentum_window: parsedMomentumWindow,
        combined_mode: combinedMode,
        transaction_cost: parsedTransactionCost,
      });
      setResult(response);
    } catch (err) {
      setError(getApiDisplayMessage(err, tr("riskReviewFailed")));
    } finally {
      setLoading(false);
    }
  }

  const riskLevel = result?.risk.risk_level ?? null;

  return (
    <SectionCard>
      <SectionHeader
        title={tr("riskGateReview")}
        description={tr("riskGateReviewDesc")}
      />

      <ul className="system-notes-list">
        <li>{tr("riskReviewDisclaimer1")}</li>
        <li>{tr("riskReviewDisclaimer2")}</li>
      </ul>

      <div className="form-grid">
        <label className="form-field">
          <span className="form-label">{tr("ticker")}</span>
          <input
            className="form-input"
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
          />
        </label>

        <label className="form-field">
          <span className="form-label">{tr("backtestStartDate")}</span>
          <input
            className="form-input"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>

        <label className="form-field">
          <span className="form-label">{tr("backtestEndDate")}</span>
          <input
            className="form-input"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>

        <label className="form-field">
          <span className="form-label">{tr("strategy")}</span>
          <select
            className="form-select"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as BacktestStrategy)}
          >
            <option value="ma_crossover">{tr("maCrossover")}</option>
            <option value="momentum">{tr("momentumStrategy")}</option>
            <option value="combined_signal">{tr("combinedSignal")}</option>
          </select>
        </label>

        {(strategy === "ma_crossover" || strategy === "combined_signal") && (
          <>
            <label className="form-field">
              <span className="form-label">{tr("shortWindow")}</span>
              <input
                className="form-input"
                type="number"
                min={2}
                value={shortWindow}
                onChange={(e) => setShortWindow(Number(e.target.value))}
              />
            </label>
            <label className="form-field">
              <span className="form-label">{tr("longWindow")}</span>
              <input
                className="form-input"
                type="number"
                min={3}
                value={longWindow}
                onChange={(e) => setLongWindow(Number(e.target.value))}
              />
            </label>
          </>
        )}

        {(strategy === "momentum" || strategy === "combined_signal") && (
          <label className="form-field">
            <span className="form-label">{tr("momentumWindow")}</span>
            <input
              className="form-input"
              type="number"
              min={5}
              max={252}
              value={momentumWindow}
              onChange={(e) => setMomentumWindow(Number(e.target.value))}
            />
          </label>
        )}

        {strategy === "combined_signal" && (
          <label className="form-field">
            <span className="form-label">{tr("combinedMode")}</span>
            <select
              className="form-select"
              value={combinedMode}
              onChange={(e) => setCombinedMode(e.target.value as CombinedMode)}
            >
              <option value="conservative">{tr("conservative")}</option>
              <option value="aggressive">{tr("aggressive")}</option>
            </select>
          </label>
        )}

        <label className="form-field">
          <span className="form-label">
            {tr("transactionCost")}
            <span className="form-label__hint">{tr("transactionCostHelper")}</span>
          </span>
          <input
            className="form-input"
            type="number"
            min={0}
            step={0.0001}
            value={transactionCost}
            onChange={(e) => setTransactionCost(e.target.value)}
          />
        </label>
      </div>

      <Button onClick={handleSubmit} disabled={loading}>
        {loading ? tr("running") : tr("riskReviewRun")}
      </Button>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingState message={tr("toolResultsLoading")} />}
      {!loading && !result && !error && (
        <EmptyState
          title={tr("toolResultsEmptyTitle")}
          description={tr("toolResultsEmptyDescription")}
        />
      )}

      {result && riskLevel !== null && (
        <>
          <div
            className={`risk-review-hero risk-review-hero--level-${riskLevel}`}
            role="status"
            aria-label={tr("riskGateRiskLevel")}
          >
            <p className="risk-review-hero__eyebrow">{tr("riskGateRiskLevel")}</p>
            <p className="risk-review-hero__level">L{riskLevel}</p>
            <p className="risk-review-hero__label">
              {translateRiskLabel(language, result.risk.risk_label)}
            </p>
            <p className="risk-review-hero__action">
              {tr("riskReviewAllowedAction")}:{" "}
              {translateAllowedAction(language, result.risk.allowed_action)}
            </p>
            <p className="risk-review-hero__meta">
              {result.ticker} · {result.strategy} · {result.data_source}
            </p>
          </div>

          <section aria-label={tr("riskReviewComponents")}>
            <h3 className="risk-review-section-title">{tr("riskReviewComponents")}</h3>
            <div className="risk-review-components">
              {COMPONENT_ORDER.map((key) => {
                const level = result.risk.component_levels[key] ?? 1;
                return (
                  <div
                    key={key}
                    className={`risk-review-component risk-review-component--level-${level}`}
                  >
                    <span className="risk-review-component__name">
                      {tr(COMPONENT_LABEL_KEYS[key])}
                    </span>
                    <span className="risk-review-component__level">L{level}</span>
                  </div>
                );
              })}
            </div>
          </section>

          <section aria-label={tr("riskGateReasons")}>
            <h3 className="risk-review-section-title">{tr("riskGateReasons")}</h3>
            <ul className="risk-review-reasons">
              {result.risk.risk_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </section>
        </>
      )}
    </SectionCard>
  );
}
