"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import NewsSentimentPanel from "@/components/features/insights/NewsSentimentPanel";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function AiInsightsPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard className="ai-insights-hero">
        <SectionHeader
          level={1}
          title={tr("aiInsightsPageTitle")}
          description={tr("aiInsightsPageDesc")}
        />
        <p className="ai-insights-hero__note">{tr("newsSentimentDisclaimerFull")}</p>
        <div className="ai-insights-hero__watchlist">
          <p className="section-meta">{tr("aiInsightsWatchlistHint")}</p>
          <p className="section-meta">{tr("aiInsightsWatchlistContrast")}</p>
          <Link href="/market-watch" className="btn btn--ghost">
            {tr("aiInsightsWatchlistCta")}
          </Link>
        </div>
      </SectionCard>

      <SectionCard className="ai-insights-workbench">
        <NewsSentimentPanel defaultTicker="SPY" />
      </SectionCard>
    </AppShell>
  );
}
