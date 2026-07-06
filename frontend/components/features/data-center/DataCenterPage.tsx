"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
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
import { getDataSourceStatus } from "@/lib/api";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { DataSourceStatusResponse } from "@/types/market";

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

export default function DataCenterPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [providerStatus, setProviderStatus] = useState<DataSourceStatusResponse | null>(
    null
  );
  const [providerStatusLoading, setProviderStatusLoading] = useState(true);
  const [providerStatusError, setProviderStatusError] = useState<string | null>(null);

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

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("dataCenter")} description={tr("dataCenterPageDesc")} />
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
            <p className="section-meta">
              <strong>{tr("dcActiveProvider")}:</strong>{" "}
              <code>{providerStatus.active_provider}</code>
            </p>
            <p className="section-meta">{tr("dcProvidersList")}</p>
            <div className="workspace-modules">
              {providerStatus.providers.map((provider) => (
                <article key={provider.name} className="module-card">
                  <div className="module-card__header">
                    <h3 className="module-card__title">{provider.name}</h3>
                    <StatusBadge
                      label={providerApiStatusLabel(provider.status, tr)}
                      variant={providerApiStatusVariant(provider.status)}
                    />
                  </div>
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
                </article>
              ))}
            </div>
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
