"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  evaluatePaperTrading,
  executePaperTrading,
  resetPaperAccount,
} from "@/lib/api";
import {
  formatMetricPercent,
  getDrawdownTone,
  getReturnTone,
} from "@/lib/formatters";
import {
  paperRiskVariant,
  t,
  translateAllowedAction,
  translateBackendText,
  translateConfidence,
  translatePaperAction,
  translateRiskLabel,
  translateStrategyName,
  type Language,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { BacktestStrategy, CombinedMode, PaperTradingResponse } from "@/types/market";

const DEFAULT_START_DATE = "2022-01-01";
const DEFAULT_TICKER = "AAPL";
const DEFAULT_SHORT_WINDOW = 20;
const DEFAULT_LONG_WINDOW = 60;
const DEFAULT_MOMENTUM_WINDOW = 60;
const DEFAULT_TRANSACTION_COST = 0.0005;

function paperActionVariant(action: string): "buy" | "sell" | "neutral" | "warning" {
  switch (action) {
    case "BUY":
      return "buy";
    case "SELL":
      return "sell";
    case "HOLD":
      return "warning";
    default:
      return "neutral";
  }
}

function validatePaperParams(
  tr: (key: import("@/lib/i18n").TranslationKey) => string,
  params: {
    ticker: string;
    strategy: BacktestStrategy;
    shortWindow: number;
    longWindow: number;
    momentumWindow: number;
    transactionCost: number;
  }
): string | null {
  const normalizedTicker = params.ticker.trim().toUpperCase();
  if (!normalizedTicker) {
    return tr("tickerEmpty");
  }
  if (params.strategy === "ma_crossover" || params.strategy === "combined_signal") {
    if (!Number.isFinite(params.shortWindow) || !Number.isFinite(params.longWindow)) {
      return tr("shortLongInvalid");
    }
    if (params.shortWindow >= params.longWindow) {
      return tr("shortLessThanLong");
    }
  }
  if (params.strategy === "momentum" || params.strategy === "combined_signal") {
    if (!Number.isFinite(params.momentumWindow)) {
      return tr("momentumInvalid");
    }
    if (params.momentumWindow < 5 || params.momentumWindow > 252) {
      return tr("momentumRange");
    }
  }
  if (!Number.isFinite(params.transactionCost) || params.transactionCost < 0) {
    return tr("transactionCostInvalid");
  }
  return null;
}

function buildRequestBody(
  language: Language,
  state: {
    ticker: string;
    startDate: string;
    endDate: string;
    strategy: BacktestStrategy;
    shortWindow: number;
    longWindow: number;
    momentumWindow: number;
    combinedMode: CombinedMode;
    transactionCost: number;
    notes: string;
  }
) {
  const normalizedTicker = state.ticker.trim().toUpperCase();
  return {
    ticker: normalizedTicker,
    start_date: state.startDate,
    end_date: state.endDate || undefined,
    strategy: state.strategy,
    short_window:
      state.strategy === "ma_crossover" || state.strategy === "combined_signal"
        ? state.shortWindow
        : undefined,
    long_window:
      state.strategy === "ma_crossover" || state.strategy === "combined_signal"
        ? state.longWindow
        : undefined,
    momentum_window:
      state.strategy === "momentum" || state.strategy === "combined_signal"
        ? state.momentumWindow
        : undefined,
    combined_mode: state.strategy === "combined_signal" ? state.combinedMode : undefined,
    transaction_cost: state.transactionCost,
    notes: state.notes.trim() || null,
  };
}

export default function PaperTradingPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [startDate, setStartDate] = useState(DEFAULT_START_DATE);
  const [endDate, setEndDate] = useState("");
  const [strategy, setStrategy] = useState<BacktestStrategy>("ma_crossover");
  const [shortWindow, setShortWindow] = useState(DEFAULT_SHORT_WINDOW);
  const [longWindow, setLongWindow] = useState(DEFAULT_LONG_WINDOW);
  const [momentumWindow, setMomentumWindow] = useState(DEFAULT_MOMENTUM_WINDOW);
  const [combinedMode, setCombinedMode] = useState<CombinedMode>("conservative");
  const [transactionCost, setTransactionCost] = useState(String(DEFAULT_TRANSACTION_COST));
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<PaperTradingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const formState = {
    ticker,
    startDate,
    endDate,
    strategy,
    shortWindow: Number(shortWindow),
    longWindow: Number(longWindow),
    momentumWindow: Number(momentumWindow),
    combinedMode,
    transactionCost: Number(transactionCost),
    notes,
  };

  async function handleEvaluate() {
    const validationError = validatePaperParams(tr, {
      ticker,
      strategy,
      shortWindow: Number(shortWindow),
      longWindow: Number(longWindow),
      momentumWindow: Number(momentumWindow),
      transactionCost: Number(transactionCost),
    });
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setActionMessage(null);
    try {
      const response = await evaluatePaperTrading(buildRequestBody(language, formState));
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("paperEvaluateFailed"));
    } finally {
      setLoading(false);
    }
  }

  async function handleExecute() {
    const validationError = validatePaperParams(tr, {
      ticker,
      strategy,
      shortWindow: Number(shortWindow),
      longWindow: Number(longWindow),
      momentumWindow: Number(momentumWindow),
      transactionCost: Number(transactionCost),
    });
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await executePaperTrading(buildRequestBody(language, formState));
      setResult(response);
      setActionMessage(
        translateBackendText(language, response.execution_message ?? tr("paperNoTrade"))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("paperExecuteFailed"));
    } finally {
      setLoading(false);
    }
  }

  async function handleReset() {
    if (!window.confirm(tr("paperResetConfirm"))) {
      return;
    }
    setLoading(true);
    setError(null);
    setActionMessage(null);
    try {
      await resetPaperAccount();
      setResult(null);
      setActionMessage(tr("paperReset"));
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("paperResetFailed"));
    } finally {
      setLoading(false);
    }
  }

  const account = result?.account;
  const signal = result?.today_signal;
  const risk = result?.risk;

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("paperTrading")} description={tr("paperTradingDesc")} />
        <p className="section-meta">{tr("paperTradingNote")}</p>

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
                  value={shortWindow}
                  onChange={(e) => setShortWindow(Number(e.target.value))}
                />
              </label>
              <label className="form-field">
                <span className="form-label">{tr("longWindow")}</span>
                <input
                  className="form-input"
                  type="number"
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
            <span className="form-label">{tr("transactionCost")}</span>
            <input
              className="form-input"
              type="number"
              step="0.0001"
              value={transactionCost}
              onChange={(e) => setTransactionCost(e.target.value)}
            />
          </label>
        </div>

        <label className="form-field paper-notes-field">
          <span className="form-label">{tr("paperNotes")}</span>
          <textarea
            className="form-textarea"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={tr("paperNotesPlaceholder")}
          />
        </label>

        <div className="button-row">
          <Button onClick={handleEvaluate} disabled={loading} primary>
            {loading ? tr("running") : tr("paperEvaluate")}
          </Button>
          <Button onClick={handleExecute} disabled={loading || !result}>
            {loading ? tr("running") : tr("paperExecute")}
          </Button>
          <Button onClick={handleReset} disabled={loading} className="btn--ghost">
            {tr("paperReset")}
          </Button>
        </div>

        {error && <ErrorAlert message={error} />}
        {actionMessage && <p className="section-meta paper-action-message">{actionMessage}</p>}
      </SectionCard>

      {loading && !result ? <LoadingState message={tr("running")} /> : null}

      {result && signal && risk && account ? (
        <>
          <div className="paper-grid">
            <SectionCard>
              <SectionHeader title={tr("paperTodaySignal")} />
              <div className="paper-signal-row">
                <StatusBadge
                  label={translatePaperAction(language, signal.paper_action)}
                  variant={paperActionVariant(signal.paper_action)}
                />
                <StatusBadge
                  label={`${tr("paperRiskLevel")} ${risk.risk_level} · ${translateRiskLabel(language, risk.risk_label)}`}
                  variant={paperRiskVariant(risk.risk_level)}
                />
              </div>
              <dl className="paper-kv">
                <div>
                  <dt>{tr("tradeDate")}</dt>
                  <dd>{signal.date}</dd>
                </div>
                <div>
                  <dt>{tr("ticker")}</dt>
                  <dd>{signal.symbol}</dd>
                </div>
                <div>
                  <dt>{tr("strategy")}</dt>
                  <dd>{translateStrategyName(language, signal.strategy)}</dd>
                </div>
                <div>
                  <dt>{tr("paperConfidence")}</dt>
                  <dd>{translateConfidence(language, signal.confidence)}</dd>
                </div>
                <div>
                  <dt>{tr("paperTargetPosition")}</dt>
                  <dd>{signal.target_position === 1 ? tr("paperLong") : tr("paperFlat")}</dd>
                </div>
                <div>
                  <dt>{tr("paperAction")}</dt>
                  <dd>{translatePaperAction(language, signal.paper_action)}</dd>
                </div>
              </dl>
              <p className="section-meta">{translateBackendText(language, signal.reason)}</p>
            </SectionCard>

            <SectionCard>
              <SectionHeader title={tr("paperRisk")} />
              <div className="paper-signal-row">
                <StatusBadge
                  label={`L${risk.risk_level} ${translateRiskLabel(language, risk.risk_label)}`}
                  variant={paperRiskVariant(risk.risk_level)}
                />
              </div>
              <p className="section-meta">
                <strong>{tr("paperAllowedAction")}:</strong>{" "}
                {translateAllowedAction(language, risk.allowed_action)}
              </p>
              <h4 className="paper-subtitle">{tr("paperRiskReasons")}</h4>
              <ul className="paper-reason-list">
                {risk.risk_reasons.map((reason) => (
                  <li key={reason}>{translateBackendText(language, reason)}</li>
                ))}
              </ul>
            </SectionCard>
          </div>

          <SectionCard>
            <SectionHeader title={tr("paperAccount")} />
            <div className="metric-grid">
              <MetricCard
                label={tr("paperPortfolioValue")}
                value={`$${account.portfolio_value.toLocaleString()}`}
              />
              <MetricCard
                label={tr("paperUnrealizedPnl")}
                value={`$${account.unrealized_pnl.toLocaleString()}`}
                tone={getReturnTone(account.unrealized_pnl)}
              />
              <MetricCard
                label={tr("paperRealizedPnl")}
                value={`$${account.realized_pnl.toLocaleString()}`}
                tone={getReturnTone(account.realized_pnl)}
              />
              <MetricCard
                label={tr("paperCurrentDrawdown")}
                value={formatMetricPercent(account.drawdown)}
                tone={getDrawdownTone(account.drawdown)}
              />
              <MetricCard
                label={tr("paperPosition")}
                value={account.position > 0 ? tr("paperLong") : tr("paperFlat")}
              />
              <MetricCard label={tr("paperCash")} value={`$${account.cash.toLocaleString()}`} />
            </div>
            <dl className="paper-kv paper-kv--compact">
              <div>
                <dt>{tr("paperShares")}</dt>
                <dd>{account.shares}</dd>
              </div>
              <div>
                <dt>{tr("paperEntryPrice")}</dt>
                <dd>{account.entry_price ?? "—"}</dd>
              </div>
              <div>
                <dt>{tr("paperCurrentPrice")}</dt>
                <dd>{account.current_price ?? "—"}</dd>
              </div>
              {account.cooldown_until ? (
                <div>
                  <dt>{tr("paperCooldown")}</dt>
                  <dd>{account.cooldown_until}</dd>
                </div>
              ) : null}
            </dl>
          </SectionCard>

          {result.trade_journal.length > 0 ? (
            <SectionCard>
              <SectionHeader title={tr("paperTradeJournal")} />
              <DataTable className="table-scroll--trade-log">
                <thead>
                  <tr>
                    <th>{tr("tradeDate")}</th>
                    <th>{tr("tradeLogAction")}</th>
                    <th className="num">{tr("price")}</th>
                    <th className="num">{tr("paperShares")}</th>
                    <th className="num">{tr("paperRiskLevel")}</th>
                    <th>{tr("tradeLogReason")}</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trade_journal.map((trade) => (
                    <tr key={`${trade.trade_date}-${trade.action}-${trade.price}`}>
                      <td>{trade.trade_date}</td>
                      <td>
                        <StatusBadge
                          label={
                            trade.action === "BUY" ? tr("tradeBuy") : tr("tradeSell")
                          }
                          variant={trade.action === "BUY" ? "buy" : "sell"}
                        />
                      </td>
                      <td className="num">{trade.price.toFixed(2)}</td>
                      <td className="num">{trade.shares.toFixed(4)}</td>
                      <td className="num">L{trade.risk_level}</td>
                      <td>{translateBackendText(language, trade.reason)}</td>
                    </tr>
                  ))}
                </tbody>
              </DataTable>
            </SectionCard>
          ) : null}

          <p className="section-meta paper-disclaimer">
            {translateBackendText(language, result.disclaimer)}
          </p>
        </>
      ) : null}
    </AppShell>
  );
}
