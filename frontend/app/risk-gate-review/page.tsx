"use client";

import AppShell from "@/components/layout/AppShell";
import RiskGateReview from "@/components/features/risk/RiskGateReview";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function RiskGateReviewPage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <RiskGateReview />
    </AppShell>
  );
}
