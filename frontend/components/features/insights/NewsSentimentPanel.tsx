"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import {
  runNewsSentiment,
  type NewsSentimentAgreement,
  type NewsSentimentOverall,
  type NewsSentimentResponse,
} from "@/lib/api";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const SCORE_KEYS = [
  "newsSentimentScore1",
  "newsSentimentScore2",
  "newsSentimentScore3",
  "newsSentimentScore4",
  "newsSentimentScore5",
] as const;

type Props = {
  defaultTicker?: string;
};

function resolveOverall(result: NewsSentimentResponse): {
  stance: string;
  score: number;
  counts: { positive: number; neutral: number; negative: number };
} {
  const overall = result.overall;
  if (overall && typeof overall === "object") {
    const typed = overall as NewsSentimentOverall;
    return {
      stance: String(typed.stance),
      score: Number(typed.score_1_5),
      counts: {
        positive: typed.counts?.positive ?? 0,
        neutral: typed.counts?.neutral ?? 0,
        negative: typed.counts?.negative ?? 0,
      },
    };
  }
  return {
    stance: String(overall ?? "neutral"),
    score: Number(result.score_1_5 ?? 3),
    counts: { positive: 0, neutral: 0, negative: 0 },
  };
}

function formatPublishedAt(value: string | null | undefined): string {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toISOString().slice(0, 16).replace("T", " ");
}

function resolveAgreement(
  result: NewsSentimentResponse
): NewsSentimentAgreement | null {
  const top = result.agreement;
  if (top && typeof top.stance_agreement === "number") return top;
  const nested = result.summary?.agreement;
  if (nested && typeof nested.stance_agreement === "number") return nested;
  return null;
}

function formatPct(rate: number): string {
  return `${Math.round(rate * 1000) / 10}%`;
}

export default function NewsSentimentPanel({ defaultTicker = "SPY" }: Props) {
  const { tr } = useWorkspaceLanguage();
  const [ticker, setTicker] = useState(defaultTicker);
  const [pasted, setPasted] = useState("");
  const [useFinbert, setUseFinbert] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<NewsSentimentResponse | null>(null);

  async function handleRun() {
    const normalized = ticker.trim().toUpperCase();
    if (!normalized) {
      setError(tr("tickerEmpty"));
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await runNewsSentiment({
        ticker: normalized,
        paste_text: pasted.trim() || undefined,
        fetch_latest: true,
        limit: 10,
        use_finbert: useFinbert,
      });
      setResult(response);
    } catch (err) {
      setError(getApiDisplayMessage(err, tr("newsSentimentFailed")));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const overall = result ? resolveOverall(result) : null;
  const agreement = result ? resolveAgreement(result) : null;
  const score = overall?.score ?? null;
  const stance = overall?.stance ?? "neutral";

  return (
    <section
      className="news-sentiment-panel"
      aria-label={tr("newsSentimentTitle")}
      data-testid="news-sentiment-panel"
    >
      <header className="news-sentiment-panel__header">
        <h2 className="news-sentiment-panel__title">{tr("newsSentimentTitle")}</h2>
        <p className="news-sentiment-panel__subtitle">
          {tr("newsSentimentSubtitle")}
        </p>
      </header>

      <div className="news-sentiment-panel__workspace">
        <section className="news-sentiment-panel__command">
      <div className="form-grid">
        <label className="form-field">
          <span className="form-label">{tr("ticker")}</span>
          <input
            className="form-input"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            data-testid="news-sentiment-ticker"
          />
        </label>
      </div>

      <label className="form-field">
        <span className="form-label">{tr("newsSentimentPasteLabel")}</span>
        <textarea
          className="form-input news-sentiment-panel__paste"
          rows={4}
          value={pasted}
          onChange={(e) => setPasted(e.target.value)}
          placeholder={tr("newsSentimentPastePlaceholder")}
          data-testid="news-sentiment-paste"
        />
      </label>

      <label className="news-sentiment-panel__finbert">
        <input
          type="checkbox"
          checked={useFinbert}
          onChange={(e) => setUseFinbert(e.target.checked)}
          data-testid="news-sentiment-finbert"
        />
        <span>
          <strong>{tr("newsSentimentUseFinbert")}</strong>
          <span className="helper-text">{tr("newsSentimentUseFinbertHint")}</span>
        </span>
      </label>

      <Button
        primary
        onClick={handleRun}
        disabled={loading || !ticker.trim()}
        data-testid="news-sentiment-run"
      >
        {loading ? tr("running") : tr("newsSentimentRun")}
      </Button>
        </section>

        <section className="news-sentiment-panel__evidence" aria-live="polite">
      {error && <ErrorAlert message={error} />}
      {loading && <LoadingState message={tr("toolResultsLoading")} />}
      {!loading && !result && !error && (
        <EmptyState
          title={tr("toolResultsEmptyTitle")}
          description={tr("newsSentimentEmptyHint")}
        />
      )}

      {result && !loading ? (
        <div className="news-sentiment-panel__result">
          <p className="news-sentiment-panel__pit" role="note">
            {tr("newsSentimentDisclaimerFull")}
          </p>

          <div
            className={`news-sentiment-panel__score is-score-${score ?? 3}`}
            role="status"
            data-testid="news-sentiment-overall"
          >
            <span className="news-sentiment-panel__score-value">
              {score ?? 3}/5
            </span>
            <span className="news-sentiment-panel__score-label">
              {score != null ? tr(SCORE_KEYS[Math.max(0, Math.min(4, score - 1))]) : null}
            </span>
            <span className="news-sentiment-panel__overall">
              {tr(
                stance === "favourable"
                  ? "newsSentimentOverallFavourable"
                  : stance === "not_favourable"
                    ? "newsSentimentOverallNotFavourable"
                    : "newsSentimentOverallNeutral"
              )}
            </span>
          </div>

          {overall ? (
            <ul
              className="news-sentiment-panel__counts"
              aria-label={tr("newsSentimentCountsLabel")}
            >
              <li>
                <span className="is-pos">{tr("newsSentimentCountPositive")}</span>
                <strong>{overall.counts.positive}</strong>
              </li>
              <li>
                <span className="is-neu">{tr("newsSentimentCountNeutral")}</span>
                <strong>{overall.counts.neutral}</strong>
              </li>
              <li>
                <span className="is-neg">{tr("newsSentimentCountNegative")}</span>
                <strong>{overall.counts.negative}</strong>
              </li>
            </ul>
          ) : null}

          {result.summary?.text ? (
            <div className="news-sentiment-panel__summary-block">
              <h3 className="news-sentiment-panel__summary-title">
                {tr("newsSentimentSummaryTitle")}
              </h3>
              <p className="news-sentiment-panel__summary">{result.summary.text}</p>
            </div>
          ) : (
            <p className="news-sentiment-panel__summary-missing">
              {tr("newsSentimentSummaryUnavailable")}
            </p>
          )}

          {agreement ? (
            <div
              className="news-sentiment-panel__agreement"
              data-testid="news-sentiment-agreement"
              role="status"
            >
              <h3 className="news-sentiment-panel__summary-title">
                {tr("newsSentimentAgreementTitle")}
              </h3>
              <ul className="news-sentiment-panel__agreement-rates">
                <li>
                  <span>{tr("newsSentimentAgreementStance")}</span>
                  <strong data-testid="news-sentiment-agreement-stance">
                    {formatPct(agreement.stance_agreement)}
                  </strong>
                </li>
                <li>
                  <span>{tr("newsSentimentAgreementScore")}</span>
                  <strong data-testid="news-sentiment-agreement-score">
                    {formatPct(agreement.score_agreement)}
                  </strong>
                </li>
                <li>
                  <span>{tr("newsSentimentAgreementCompared")}</span>
                  <strong>{agreement.n_compared}</strong>
                </li>
              </ul>
              <p className="news-sentiment-panel__agreement-note">
                {agreement.note || tr("newsSentimentAgreementNote")}
              </p>
            </div>
          ) : null}

          {result.items.length === 0 ? (
            <p className="news-sentiment-panel__empty-items">
              {tr("newsSentimentNoItems")}
            </p>
          ) : (
            <ul className="news-sentiment-panel__items">
              {result.items.map((item, idx) => (
                <li key={`${item.headline}-${idx}`}>
                  <div className="news-sentiment-panel__item-head">
                    <span
                      className={`news-sentiment-panel__stance is-${item.stance}`}
                    >
                      {item.stance}
                      {item.score_1_5 != null ? ` · ${item.score_1_5}/5` : ""}
                    </span>
                    {item.llm_stance != null || item.llm_score_1_5 != null ? (
                      <span
                        className="news-sentiment-panel__llm-shadow"
                        title={tr("newsSentimentAgreementNote")}
                      >
                        {tr("newsSentimentLlmShadow")}: {item.llm_stance ?? "—"}
                        {item.llm_score_1_5 != null
                          ? ` · ${item.llm_score_1_5}/5`
                          : ""}
                      </span>
                    ) : null}
                    <strong>
                      {item.url ? (
                        <a href={item.url} target="_blank" rel="noreferrer">
                          {item.headline}
                        </a>
                      ) : (
                        item.headline
                      )}
                    </strong>
                  </div>
                  <p>{item.reason}</p>
                  <cite>
                    {[item.source, formatPublishedAt(item.published_at)]
                      .filter(Boolean)
                      .join(" · ")}
                  </cite>
                </li>
              ))}
            </ul>
          )}

          <p className="news-sentiment-panel__disclaimer">
            {result.summary?.disclaimer || tr("newsSentimentDisclaimerFull")}
          </p>
          {result.provider || result.classifier ? (
            <p className="news-sentiment-panel__meta">
              {[
                result.provider
                  ? `${tr("newsSentimentProvider")}: ${result.provider}`
                  : null,
                result.classifier
                  ? `${tr("newsSentimentClassifier")}: ${result.classifier}`
                  : null,
              ]
                .filter(Boolean)
                .join(" · ")}
            </p>
          ) : null}
        </div>
      ) : null}
        </section>
      </div>
    </section>
  );
}
