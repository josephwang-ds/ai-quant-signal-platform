"use client";

import { useMemo, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import {
  runModelComparison,
  type ModelComparisonResponse,
} from "@/lib/api";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const FeatureInterpretationPanels = dynamic(
  () => import("@/components/features/comparison/FeatureInterpretationPanels"),
  { ssr: false, loading: () => <LoadingState message="Loading interpretation…" /> }
);

const DEFAULT_TICKER = "SPY";
const DEFAULT_START_DATE = "2020-01-01";
const DEFAULT_N_FOLDS = 4;

/**
 * Feature Interpretation reuses the Compare Models API.
 * Prediction / signal logic is unchanged — this page only renders importance research.
 */
export default function FeatureInterpretationPage() {
  const { language, tr } = useWorkspaceLanguage();
  const [ticker, setTicker] = useState(DEFAULT_TICKER);
  const [startDate, setStartDate] = useState(DEFAULT_START_DATE);
  const [nFolds, setNFolds] = useState(String(DEFAULT_N_FOLDS));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ModelComparisonResponse | null>(null);

  const selectedModels = useMemo(
    () => ["logistic_l2", "random_forest", "xgboost", "ridge_reg"],
    []
  );

  async function handleRun() {
    setLoading(true);
    setError(null);
    try {
      const folds = Number(nFolds);
      const response = await runModelComparison({
        ticker: ticker.trim().toUpperCase() || DEFAULT_TICKER,
        start_date: startDate,
        n_folds: Number.isFinite(folds) && folds >= 2 ? folds : DEFAULT_N_FOLDS,
        scheme: "expanding",
        models: selectedModels,
        preprocessing: "none",
        transaction_cost: 0.001,
        short_window: 20,
        long_window: 60,
        momentum_window: 60,
      });
      setResult(response);
    } catch (err) {
      setResult(null);
      setError(
        getApiDisplayMessage(
          err,
          "Feature interpretation unavailable. Invented importance is not shown."
        )
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <SectionCard>
        <SectionHeader
          level={1}
          title={tr("featureInterpTitle")}
          description={tr("featureInterpDescription")}
        />
        <p className="feature-interpretation-disclaimer feature-interpretation-disclaimer--page">
          {tr("featureInterpCausality")}
        </p>
        <p className="section-meta">
          {tr("featureInterpReuseCompare")}{" "}
          <Link href="/compare-models">{tr("navCompareModels")}</Link>
        </p>

        <div className="form-grid form-grid--compact">
          <div className="form-field">
            <label className="form-label" htmlFor="fi-ticker">
              {tr("ticker")}
            </label>
            <input
              id="fi-ticker"
              className="form-input"
              value={ticker}
              onChange={(event) => setTicker(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label className="form-label" htmlFor="fi-start">
              {tr("backtestStartDate")}
            </label>
            <input
              id="fi-start"
              className="form-input"
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.target.value)}
            />
          </div>
          <div className="form-field">
            <label className="form-label" htmlFor="fi-folds">
              {tr("modelComparisonNFolds")}
            </label>
            <input
              id="fi-folds"
              className="form-input"
              type="number"
              min={2}
              max={8}
              value={nFolds}
              onChange={(event) => setNFolds(event.target.value)}
            />
          </div>
        </div>

        <div className="page-actions">
          <Button primary disabled={loading} onClick={() => void handleRun()}>
            {loading ? tr("featureInterpRunning") : tr("featureInterpRun")}
          </Button>
        </div>
      </SectionCard>

      {loading ? <LoadingState message={tr("featureInterpLoading")} /> : null}
      {error ? (
        <ErrorAlert title={tr("featureInterpErrorTitle")} message={error} />
      ) : null}

      {!loading && !error && !result ? (
        <EmptyState
          title={tr("featureInterpEmptyTitle")}
          description={tr("featureInterpEmptyDescription")}
        />
      ) : null}

      {result ? (
        <SectionCard>
          <SectionHeader
            title={tr("featureInterpResultsTitle")}
            description={tr("featureInterpResultsDescription")}
          />
          <FeatureInterpretationPanels
            results={result.results}
            language={language}
            labels={{
              disclaimer: tr("featureInterpCausality"),
              rankingTitle: tr("featureInterpRanking"),
              methodNative: tr("featureInterpMethodNative"),
              methodPermutation: tr("featureInterpMethodPermutation"),
              methodShap: tr("featureInterpMethodShap"),
              methodCoefficient: tr("featureInterpMethodCoefficient"),
              unavailable: tr("featureInterpUnavailable"),
              consistentTitle: tr("featureInterpConsistent"),
              unstableTitle: tr("featureInterpUnstable"),
              consistentEmpty: tr("featureInterpConsistentEmpty"),
              unstableEmpty: tr("featureInterpUnstableEmpty"),
              stabilityNote: tr("featureInterpStabilityNote"),
              stabilityNeedFolds: tr("featureInterpStabilityNeedFolds"),
              stabilityUnavailable: tr("featureInterpStabilityUnavailable"),
              foldCount: tr("featureInterpFoldCount"),
              signedCoef: tr("featureInterpSignedCoef"),
              limitationsTitle: tr("featureInterpLimitations"),
            }}
          />
        </SectionCard>
      ) : null}
    </div>
  );
}
