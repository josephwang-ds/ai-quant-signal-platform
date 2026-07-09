"use client";

import Link from "next/link";
import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { Button, ErrorAlert, SectionCard, SectionHeader, StatusBadge, healthVariant } from "@/components/ui";
import { getBackendHealth, type HealthResponse } from "@/lib/api";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import {
  MODULE_CATEGORIES,
  WORKSPACE_MODULES,
  moduleStatusBadgeVariant,
  moduleStatusLabelKey,
  shouldShowModuleStatusBadge,
} from "@/lib/workspaceModules";

export default function OverviewPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  async function handleCheckBackend() {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const result = await getBackendHealth();
      setHealth(result);
    } catch {
      setHealth(null);
      setHealthError(tr("backendUnreachable"));
    } finally {
      setHealthLoading(false);
    }
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("overviewTitle")} />
        <p className="overview-intro">{tr("overviewDesc")}</p>
        <p className="overview-legend">{tr("overviewStatusLegend")}</p>
      </SectionCard>

      {MODULE_CATEGORIES.map((category) => (
        <SectionCard key={category.id}>
          <SectionHeader title={tr(category.titleKey)} />
          <div className="workspace-modules">
            {category.moduleIds.map((moduleId) => {
              const module = WORKSPACE_MODULES.find((item) => item.id === moduleId);
              if (!module) {
                return null;
              }
              const statusKey = moduleStatusLabelKey(module.status);
              const showStatus = shouldShowModuleStatusBadge(module.status);
              return (
                <article key={module.id} className="module-card">
                  <div className="module-card__header">
                    <h3 className="module-card__title">{tr(module.titleKey)}</h3>
                    {showStatus ? (
                      <StatusBadge
                        label={tr(statusKey)}
                        variant={moduleStatusBadgeVariant(module.status)}
                      />
                    ) : null}
                  </div>
                  <p className="module-card__desc">{tr(module.overviewDescKey)}</p>
                  <Link href={module.href} className="module-card__link">
                    {tr("openModule")} →
                  </Link>
                  {module.legacyAnchor ? (
                    <Link href={`/legacy#${module.legacyAnchor}`} className="module-card__link">
                      {tr("openLegacyDemo")} →
                    </Link>
                  ) : null}
                </article>
              );
            })}
          </div>
        </SectionCard>
      ))}

      <SectionCard>
        <SectionHeader title={tr("categorySystemNotes")} />
        <div className="health-row">
          <div className="health-row__info">
            <p className="section-meta">{tr("backendHealthHint")}</p>
            {health && (
              <div className="health-row__status">
                <span className="health-row__label">{tr("status")}:</span>
                <StatusBadge label={health.status} variant={healthVariant(health.status)} />
                <span className="health-row__service">
                  {tr("service")}: {health.service}
                </span>
              </div>
            )}
          </div>
          <Button onClick={handleCheckBackend} disabled={healthLoading}>
            {healthLoading ? tr("checking") : tr("checkBackend")}
          </Button>
        </div>
        {healthError && <ErrorAlert message={healthError} />}
        <ul className="system-notes-list">
          <li>{tr("systemCurrentDataSource")}</li>
          <li>{tr("systemFutureDatabase")}</li>
          <li>{tr("systemFutureCache")}</li>
          <li>{tr("systemNotAdvice")}</li>
        </ul>
      </SectionCard>
    </AppShell>
  );
}
