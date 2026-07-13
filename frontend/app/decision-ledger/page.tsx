"use client";

import AppShell from "@/components/layout/AppShell";
import DecisionLedgerPanel from "@/components/features/executive/DecisionLedgerPanel";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function DecisionLedgerPage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <DecisionLedgerPanel />
    </AppShell>
  );
}
