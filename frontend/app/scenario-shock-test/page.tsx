"use client";

import AppShell from "@/components/layout/AppShell";
import ScenarioShockTestPanel from "@/components/features/executive/ScenarioShockTestPanel";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function ScenarioShockTestPage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <ScenarioShockTestPanel />
    </AppShell>
  );
}
