"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { Button, ErrorAlert, SectionCard, SectionHeader, StatusBadge, healthVariant } from "@/components/ui";
import { getBackendHealth, getPaperAccount, type HealthResponse } from "@/lib/api";
import { getApiUserMessage } from "@/lib/apiRequest";
import { paperRiskVariant, translateRiskLabel } from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import {
  MODULE_CATEGORIES,
  WORKSPACE_MODULES,
  moduleStatusBadgeVariant,
  moduleStatusLabelKey,
  shouldShowModuleStatusBadge,
} from "@/lib/workspaceModules";
import type { PaperAccount } from "@/types/market";

export default function OverviewPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [paperAccount, setPaperAccount] = useState<PaperAccount | null>(null);

  useEffect(() => {
    getPaperAccount()
      .then((response) => setPaperAccount(response.account))
      .catch(() => setPaperAccount(null));
  }, []);

  async function handleCheckBackend() {
    setHealthLoading(true);
    setHealthError(null);
    try {
      const result = await getBackendHealth();
      setHealth(result);
    } catch (error) {
      setHealth(null);
      setHealthError(getApiUserMessage(error, tr("backendUnreachable")));
    } finally {
      setHealthLoading(false);
    }
  }

  const upcomingModules = WORKSPACE_MODULES.filter(
    (module) => module.status === "planned" || module.status === "comingLater"
  );

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr("overviewTitle")} />
        <p className="overview-intro">{tr("overviewDesc")}</p>
        <p className="overview-legend">{tr("overviewStatusLegend")}</p>
      </SectionCard>

      <SectionCard>
        <SectionHeader
          title={tr("overviewPaperAccount")}
          description={tr("overviewPaperAccountDesc")}
        />
        {paperAccount?.ticker ? (
          <div className="overview-paper">
            <div className="overview-paper__row">
              <span>
                {paperAccount.ticker} · {paperAccount.strategy}
              </span>
              {paperAccount.last_risk_level && paperAccount.last_risk_label ? (
                <StatusBadge
                  label={`L${paperAccount.last_risk_level} ${translateRiskLabel(language, paperAccount.last_risk_label)}`}
                  variant={paperRiskVariant(paperAccount.last_risk_level)}
                />
              ) : null}
            </div>
            <p className="section-meta">
              {tr("paperPortfolioValue")}: ${paperAccount.portfolio_value.toLocaleString()} ·{" "}
              {tr("paperPosition")}: {paperAccount.position > 0 ? tr("paperLong") : tr("paperFlat")}
            </p>
          </div>
        ) : (
          <p className="section-meta">{tr("overviewPaperNotEvaluated")}</p>
        )}
        <Link href="/paper-trading" className="module-card__link">
          {tr("overviewOpenPaperTrading")} →
        </Link>
      </SectionCard>

      {MODULE_CATEGORIES.map((category) => {
        const activeModules = category.moduleIds
          .map((moduleId) => WORKSPACE_MODULES.find((item) => item.id === moduleId))
          .filter(
            (module): module is (typeof WORKSPACE_MODULES)[number] =>
              module != null && module.status === "active"
          );
        if (activeModules.length === 0) {
          return null;
        }
        return (
          <SectionCard key={category.id}>
            <SectionHeader title={tr(category.titleKey)} />
            <div className="workspace-modules">
              {activeModules.map((module) => {
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
        );
      })}

      {upcomingModules.length > 0 ? (
          <SectionCard>
            <details className="overview-coming-soon">
              <summary>{tr("comingSoonTitle")}</summary>
              <div className="workspace-modules">
                {upcomingModules.map((module) => {
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
                        <Link
                          href={`/legacy#${module.legacyAnchor}`}
                          className="module-card__link"
                        >
                          {tr("openLegacyDemo")} →
                        </Link>
                      ) : null}
                    </article>
                  );
                })}
              </div>
            </details>
          </SectionCard>
        ) : null}

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
