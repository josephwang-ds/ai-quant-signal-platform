"use client";

import AppShell from "@/components/layout/AppShell";
import StrategyHealthScorePanel from "@/components/features/executive/StrategyHealthScorePanel";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function StrategyHealthScorePage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <StrategyHealthScorePanel />
    </AppShell>
  );
}
