"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import {
  Button,
  EmptyState,
  ErrorAlert,
  SectionCard,
  SectionHeader,
  StatusBadge,
  healthVariant,
} from "@/components/ui";
import { getBackendHealth, getPaperAccount, type HealthResponse } from "@/lib/api";
import { getApiUserMessage } from "@/lib/apiRequest";
import { paperRiskVariant, translateRiskLabel } from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";
import type { PaperAccount } from "@/types/market";

const ENTRY_CARDS = [
  {
    href: "/compare-models",
    titleKey: "dashboardCardCompareTitle" as const,
    valueKey: "dashboardCardCompareValue" as const,
    ctaKey: "dashboardCardCompareCta" as const,
  },
  {
    href: "/risk-gate-review",
    titleKey: "dashboardCardRiskTitle" as const,
    valueKey: "dashboardCardRiskValue" as const,
    ctaKey: "dashboardCardRiskCta" as const,
  },
  {
    href: "/",
    titleKey: "dashboardCardIdeasTitle" as const,
    valueKey: "dashboardCardIdeasValue" as const,
    ctaKey: "dashboardCardIdeasCta" as const,
  },
];

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

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader
          level={1}
          title={tr("overviewTitle")}
          description={tr("overviewDesc")}
        />

        <div className="dashboard-entry-grid" role="list">
          {ENTRY_CARDS.map((card) => (
            <article key={card.href} className="dashboard-entry-card" role="listitem">
              <h3 className="dashboard-entry-card__title">{tr(card.titleKey)}</h3>
              <p className="dashboard-entry-card__value">{tr(card.valueKey)}</p>
              <Link href={card.href} className="dashboard-entry-card__cta">
                {tr(card.ctaKey)} →
              </Link>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard>
        <SectionHeader
          title={tr("dashboardRecentTitle")}
          description={tr("dashboardRecentDesc")}
        />
        {paperAccount?.ticker ? (
          <div className="dashboard-recent">
            <div className="dashboard-recent__row">
              <div>
                <p className="dashboard-recent__label">{tr("dashboardRecentLastReview")}</p>
                <p className="dashboard-recent__primary">
                  {paperAccount.ticker} · {paperAccount.strategy}
                </p>
                <p className="section-meta">
                  {tr("paperPortfolioValue")}: $
                  {paperAccount.portfolio_value.toLocaleString()} · {tr("paperPosition")}:{" "}
                  {paperAccount.position > 0 ? tr("paperLong") : tr("paperFlat")}
                </p>
              </div>
              {paperAccount.last_risk_level && paperAccount.last_risk_label ? (
                <StatusBadge
                  label={`L${paperAccount.last_risk_level} ${translateRiskLabel(language, paperAccount.last_risk_label)}`}
                  variant={paperRiskVariant(paperAccount.last_risk_level)}
                />
              ) : null}
            </div>
            <div className="dashboard-recent__actions">
              <Link href="/risk-gate-review" className="module-card__link">
                {tr("dashboardRecentOpenRisk")} →
              </Link>
              <Link href="/paper-trading" className="module-card__link">
                {tr("overviewOpenPaperTrading")} →
              </Link>
              <Link href="/research/ma-crossover-spy" className="module-card__link">
                {tr("dashboardRecentOpenSample")} →
              </Link>
            </div>
          </div>
        ) : (
          <EmptyState
            title={tr("dashboardRecentEmptyTitle")}
            description={tr("dashboardRecentEmptyDesc")}
            action={
              <Link href="/compare-models" className="btn btn--primary">
                {tr("dashboardCardCompareCta")}
              </Link>
            }
          />
        )}
      </SectionCard>

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
