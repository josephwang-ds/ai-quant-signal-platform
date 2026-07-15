"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  ASSET_CLASS_ROWS,
  coverageStatusBadgeVariant,
  coverageStatusLabelKey,
  PLANNED_PROVIDER_CARDS,
  SYMBOL_FORMAT_ROWS,
  YAHOO_USE_CASE_KEYS,
} from "@/lib/dataCenterConfig";
import { getDataSourceStatus, probePriceData } from "@/lib/api";
import {
  getDataSourcePreference,
  isMarketDataSource,
  MARKET_DATA_SOURCES,
  setDataSourcePreference,
  type MarketDataSource,
} from "@/lib/dataSourcePreference";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { TranslationKey } from "@/lib/i18n";
import type {
  DataSourceStatusResponse,
  ResearchDataProviderStatus,
} from "@/types/market";

function isResearchProviderStatus(
  provider: DataSourceStatusResponse["providers"][number]
): provider is ResearchDataProviderStatus {
  return "installed" in provider && "supported_assets" in provider;
}

function providerApiStatusLabel(
  status: string,
  tr: (key: "statusActive" | "statusPlanned") => string
): string {
  if (status === "active") {
    return tr("statusActive");
  }
  if (status === "planned") {
    return tr("statusPlanned");
  }
  return status;
}

function providerApiStatusVariant(
  status: string
): "success" | "info" | "neutral" {
  if (status === "active") {
    return "success";
  }
  if (status === "planned") {
    return "info";
  }
  return "neutral";
}

const PREFERRED_SOURCE_LABEL_KEYS: Record<MarketDataSource, TranslationKey> = {
  auto: "dcPreferredSourceOptionAuto",
  akshare: "dcPreferredSourceOptionAkshare",
  yahoo: "dcPreferredSourceOptionYahoo",
  stooq: "dcPreferredSourceOptionStooq",
};

export default function DataCenterPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [providerStatus, setProviderStatus] = useState<DataSourceStatusResponse | null>(
    null
  );
  const [providerStatusLoading, setProviderStatusLoading] = useState(true);
  const [providerStatusError, setProviderStatusError] = useState<string | null>(null);
  const [preferredSource, setPreferredSource] = useState<MarketDataSource>("auto");
  const [probeLoading, setProbeLoading] = useState(false);
  const [probeResult, setProbeResult] = useState<string | null>(null);
  const [probeError, setProbeError] = useState<string | null>(null);

  useEffect(() => {
    setPreferredSource(getDataSourcePreference());
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadProviderStatus() {
      setProviderStatusLoading(true);
      setProviderStatusError(null);

      try {
        const data = await getDataSourceStatus();
        if (!cancelled) {
          setProviderStatus(data);
        }
      } catch (error) {
        if (!cancelled) {
          setProviderStatusError(
            error instanceof Error ? error.message : "Unknown error"
          );
        }
      } finally {
        if (!cancelled) {
          setProviderStatusLoading(false);
        }
      }
    }

    void loadProviderStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  function handlePreferredSourceChange(value: string) {
    if (!isMarketDataSource(value)) {
      return;
    }
    setPreferredSource(value);
    setDataSourcePreference(value);
    setProbeResult(null);
    setProbeError(null);
  }

  async function handleProbe() {
    setProbeLoading(true);
    setProbeResult(null);
    setProbeError(null);
    try {
      const data = await probePriceData("AAPL", "2024-01-01", preferredSource);
      setProbeResult(
        `${tr("dcProbeSuccess")}: ${data.data_source} · rows=${data.rows} · latest=${data.latest.date}`
      );
    } catch (error) {
      setProbeError(error instanceof Error ? error.message : tr("dcProbeError"));
    } finally {
      setProbeLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("dataCenter")} description={tr("dataCenterPageDesc")} />
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcPreferredSource")} description={tr("dcPreferredSourceDesc")} />
        <div className="form-field" style={{ maxWidth: 360 }}>
          <label className="form-label" htmlFor="preferred-data-source">
            {tr("dcPreferredSource")}
          </label>
          <select
            id="preferred-data-source"
            className="form-select"
            value={preferredSource}
            onChange={(event) => handlePreferredSourceChange(event.target.value)}
          >
            {MARKET_DATA_SOURCES.map((source) => (
              <option key={source} value={source}>
                {tr(PREFERRED_SOURCE_LABEL_KEYS[source])}
              </option>
            ))}
          </select>
        </div>
        <div className="button-row" style={{ marginTop: 12 }}>
          <Button
            className="btn--ghost"
            onClick={() => void handleProbe()}
            disabled={probeLoading}
          >
            {probeLoading ? tr("dcProbeLoading") : tr("dcProbeSource")}
          </Button>
          {probeResult ? <p className="section-meta">{probeResult}</p> : null}
        </div>
        {probeError ? (
          <ErrorAlert title={tr("dcProbeError")} message={probeError} />
        ) : null}
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcLiveProviderStatus")} />
        {providerStatusLoading ? (
          <LoadingState message={tr("dcLoadingProviderStatus")} />
        ) : null}
        {providerStatusError ? (
          <>
            <ErrorAlert
              title={tr("dcProviderStatusError")}
              message={providerStatusError}
            />
            <p className="section-meta">{tr("dcStaticDocsFallback")}</p>
          </>
        ) : null}
        {providerStatus ? (
          <>
            {providerStatus.routing_mode ? (
              <p className="section-meta">
                <strong>{tr("dcRoutingMode")}:</strong>{" "}
                <code>{providerStatus.routing_mode}</code>
              </p>
            ) : null}
            {providerStatus.active_provider ? (
              <p className="section-meta">
                <strong>{tr("dcActiveProvider")}:</strong>{" "}
                <code>{providerStatus.active_provider}</code>
              </p>
            ) : null}
            {providerStatus.fallback_chain?.default?.length ? (
              <p className="section-meta">
                fallback: <code>{providerStatus.fallback_chain.default.join(" → ")}</code>
              </p>
            ) : null}
            {providerStatus.symbol_examples?.length ? (
              <p className="section-meta">
                <strong>{tr("dcSymbolExamples")}:</strong>{" "}
                {providerStatus.symbol_examples.map((symbol) => (
                  <code key={symbol} style={{ marginRight: 8 }}>
                    {symbol}
                  </code>
                ))}
              </p>
            ) : null}
            <p className="section-meta">{tr("dcProvidersList")}</p>
            <div className="workspace-modules">
              {providerStatus.providers.map((provider) => (
                <article key={provider.name} className="module-card">
                  <div className="module-card__header">
                    <h3 className="module-card__title">{provider.name}</h3>
                    {isResearchProviderStatus(provider) ? (
                      <StatusBadge
                        label={
                          provider.installed && provider.configured
                            ? tr("statusActive")
                            : tr("statusPlanned")
                        }
                        variant={
                          provider.installed && provider.configured
                            ? "success"
                            : "info"
                        }
                      />
                    ) : (
                      <StatusBadge
                        label={providerApiStatusLabel(provider.status, tr)}
                        variant={providerApiStatusVariant(provider.status)}
                      />
                    )}
                  </div>
                  {isResearchProviderStatus(provider) ? (
                    <>
                      <p className="section-meta">
                        {tr("dcProviderInstalled")}:{" "}
                        {provider.installed ? tr("yes") : tr("no")} ·{" "}
                        {tr("dcProviderConfigured")}:{" "}
                        {provider.configured ? tr("yes") : tr("no")} ·{" "}
                        {tr("dcProviderLiveHealth")}:{" "}
                        {provider.live_health_checked ? tr("yes") : tr("no")}
                      </p>
                      <ul className="system-notes-list">
                        {provider.supported_assets.map((assetClass) => (
                          <li key={assetClass}>{assetClass}</li>
                        ))}
                      </ul>
                    </>
                  ) : (
                    <>
                      {provider.asset_classes?.length ? (
                        <ul className="system-notes-list">
                          {provider.asset_classes.map((assetClass) => (
                            <li key={assetClass}>{assetClass}</li>
                          ))}
                        </ul>
                      ) : null}
                      {provider.note ? (
                        <p className="section-meta">{provider.note}</p>
                      ) : null}
                    </>
                  )}
                </article>
              ))}
            </div>
            {providerStatus.notes?.map((note) => (
              <p key={note} className="section-meta">
                {note}
              </p>
            ))}
          </>
        ) : null}
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcCurrentActiveProvider")} />
        <article className="module-card">
          <div className="module-card__header">
            <h3 className="module-card__title">{tr("dcProviderYahoo")}</h3>
            <StatusBadge label={tr("statusActive")} variant="success" />
          </div>
          <ul className="system-notes-list">
            {YAHOO_USE_CASE_KEYS.map((key) => (
              <li key={key}>{tr(key)}</li>
            ))}
          </ul>
          <p className="section-meta">{tr("dcYahooNote")}</p>
        </article>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcAssetClassCoverage")} />
        <DataTable className="table-scroll">
          <thead>
            <tr>
              <th>{tr("dcColAssetClass")}</th>
              <th>{tr("dcColMarket")}</th>
              <th>{tr("dcColExamples")}</th>
              <th>{tr("dcColCurrentSource")}</th>
              <th>{tr("dcColStatus")}</th>
              <th>{tr("dcColNotes")}</th>
            </tr>
          </thead>
          <tbody>
            {ASSET_CLASS_ROWS.map((row) => (
              <tr key={row.id}>
                <td>{tr(row.assetClassKey)}</td>
                <td>{tr(row.marketKey)}</td>
                <td>{row.examples}</td>
                <td>{tr(row.sourceKey)}</td>
                <td>
                  <StatusBadge
                    label={tr(coverageStatusLabelKey(row.status))}
                    variant={coverageStatusBadgeVariant(row.status)}
                  />
                </td>
                <td>{row.notesKey ? tr(row.notesKey) : tr("na")}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcPlannedProviders")} />
        <div className="workspace-modules">
          {PLANNED_PROVIDER_CARDS.map((provider) => (
            <article key={provider.id} className="module-card">
              <div className="module-card__header">
                <h3 className="module-card__title">{tr(provider.titleKey)}</h3>
                <StatusBadge
                  label={tr(coverageStatusLabelKey(provider.status))}
                  variant={coverageStatusBadgeVariant(provider.status)}
                />
              </div>
              <p className="module-card__desc">{tr(provider.descKey)}</p>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcSymbolFormatGuide")} />
        <DataTable>
          <thead>
            <tr>
              <th>{tr("dcColFormatType")}</th>
              <th>{tr("dcColSymbolExample")}</th>
            </tr>
          </thead>
          <tbody>
            {SYMBOL_FORMAT_ROWS.map((row) => (
              <tr key={row.id}>
                <td>{tr(row.labelKey)}</td>
                <td>
                  <code>{row.example}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("dcFutureDataArchitecture")} />
        <ul className="system-notes-list">
          <li>{tr("dcArchDataSource")}</li>
          <li>{tr("dcArchNormalize")}</li>
          <li>{tr("dcArchSchema")}</li>
          <li>{tr("dcCachePlanned")}</li>
          <li>{tr("dcDatabasePlanned")}</li>
        </ul>
      </SectionCard>
    </AppShell>
  );
}
