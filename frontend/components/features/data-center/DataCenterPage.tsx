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
  PRICE_ONLY_ROWS,
  RESEARCH_READY_ROWS,
  SYMBOL_FORMAT_ROWS,
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
      const probeSymbol =
        preferredSource === "akshare" ? "000001.SZ" : "AAPL";
      const data = await probePriceData(
        probeSymbol,
        "2024-01-01",
        preferredSource
      );
      setProbeResult(
        `${tr("dcProbeSuccess")}: ${probeSymbol} · ${data.data_source} · rows=${data.rows} · latest=${data.latest.date}`
      );
    } catch (error) {
      setProbeError(error instanceof Error ? error.message : tr("dcProbeError"));
    } finally {
      setProbeLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard className="data-center-hero">
        <SectionHeader
          level={1}
          title={tr("dataCenter")}
          description={tr("dataCenterPageDesc")}
        />
        <div className="data-center-flow" aria-label={tr("dcCurrentDataFlow")}>
          <span>{tr("dcFlowSource")}</span>
          <span aria-hidden="true">→</span>
          <span>{tr("dcFlowNormalize")}</span>
          <span aria-hidden="true">→</span>
          <span>{tr("dcFlowSchema")}</span>
        </div>
      </SectionCard>

      <SectionCard className="data-center-control-panel">
        <SectionHeader title={tr("dcPreferredSource")} description={tr("dcPreferredSourceDesc")} />
        <div className="data-center-control-row">
          <div className="form-field">
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
          <Button
            className="btn--ghost"
            onClick={() => void handleProbe()}
            disabled={probeLoading}
          >
            {probeLoading ? tr("dcProbeLoading") : tr("dcProbeSource")}
          </Button>
        </div>
        {probeResult ? <p className="data-center-probe-result">{probeResult}</p> : null}
        {probeError ? (
          <ErrorAlert title={tr("dcProbeError")} message={probeError} />
        ) : null}
      </SectionCard>

      <SectionCard className="data-center-status-panel">
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
            <dl className="data-center-routing-summary">
              {providerStatus.routing_mode ? (
                <div>
                  <dt>{tr("dcRoutingMode")}</dt>
                  <dd><code>{providerStatus.routing_mode}</code></dd>
                </div>
              ) : null}
              {providerStatus.active_provider ? (
                <div>
                  <dt>{tr("dcActiveProvider")}</dt>
                  <dd><code>{providerStatus.active_provider}</code></dd>
                </div>
              ) : null}
              {providerStatus.fallback_chain?.default?.length ? (
                <div>
                  <dt>Fallback</dt>
                  <dd><code>{providerStatus.fallback_chain.default.join(" → ")}</code></dd>
                </div>
              ) : null}
              {providerStatus.symbol_examples?.length ? (
                <div>
                  <dt>{tr("dcSymbolExamples")}</dt>
                  <dd className="data-center-symbols">
                    {providerStatus.symbol_examples.map((symbol) => (
                      <code key={symbol}>{symbol}</code>
                    ))}
                  </dd>
                </div>
              ) : null}
            </dl>
            <p className="section-meta">{tr("dcProvidersList")}</p>
            <div className="workspace-modules data-center-provider-grid">
              {providerStatus.providers
                .filter((provider) =>
                  isResearchProviderStatus(provider)
                    ? provider.installed && provider.configured
                    : provider.status === "active"
                )
                .map((provider) => (
                <article key={provider.name} className="module-card">
                  <div className="module-card__header">
                    <h3 className="module-card__title">{provider.name}</h3>
                    {isResearchProviderStatus(provider) ? (
                      <StatusBadge
                        label={tr("statusActive")}
                        variant="success"
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
          </>
        ) : null}
      </SectionCard>

      <SectionCard
        className="data-center-reference-panel"
        data-testid="research-ready-data"
      >
        <SectionHeader
          title={tr("dcResearchReadyTitle")}
          description={tr("dcResearchReadyDesc")}
        />
        <DataTable className="table-scroll">
          <thead>
            <tr>
              <th>{tr("dcColAssetClass")}</th>
              <th>{tr("dcColReadiness")}</th>
              <th>{tr("dcColSupportDetail")}</th>
            </tr>
          </thead>
          <tbody>
            {RESEARCH_READY_ROWS.map((row) => (
              <tr key={row.id} data-readiness={row.readiness}>
                <td>{tr(row.assetClassKey)}</td>
                <td>
                  <StatusBadge label={tr(row.supportKey)} variant="success" />
                </td>
                <td>{tr(row.detailKey)}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </SectionCard>

      <SectionCard
        className="data-center-reference-panel data-center-reference-panel--muted"
        data-testid="price-only-coverage"
      >
        <SectionHeader
          title={tr("dcPriceOnlyTitle")}
          description={tr("dcPriceOnlyDesc")}
        />
        <DataTable>
          <thead>
            <tr>
              <th>{tr("dcColAssetClass")}</th>
              <th>{tr("dcColExamples")}</th>
            </tr>
          </thead>
          <tbody>
            {PRICE_ONLY_ROWS.map((row) => (
              <tr key={row.id}>
                <td>{tr(row.labelKey)}</td>
                <td>
                  <code>{row.examples}</code>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      </SectionCard>

      <SectionCard className="data-center-reference-panel">
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

    </AppShell>
  );
}
