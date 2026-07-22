"use client";

import AppShell from "@/components/layout/AppShell";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import NewsSentimentPanel from "@/components/features/insights/NewsSentimentPanel";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function AiInsightsPage() {
  const { language, setLanguage, tr } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader
          title={tr("aiInsightsPageTitle")}
          description={tr("aiInsightsPageDesc")}
        />
        <p className="section-meta">{tr("newsSentimentDisclaimerFull")}</p>
      </SectionCard>

      <SectionCard>
        <NewsSentimentPanel defaultTicker="SPY" />
      </SectionCard>
    </AppShell>
  );
}
