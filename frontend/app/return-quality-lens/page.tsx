"use client";

import AppShell from "@/components/layout/AppShell";
import ReturnQualityLens from "@/components/features/executive/ReturnQualityLens";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function ReturnQualityLensPage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <ReturnQualityLens />
    </AppShell>
  );
}
