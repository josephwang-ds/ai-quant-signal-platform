"use client";

import AppShell from "@/components/layout/AppShell";
import DecisionRoomPanel from "@/components/features/decision-room/DecisionRoomPanel";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function DecisionRoomPage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <DecisionRoomPanel />
    </AppShell>
  );
}
