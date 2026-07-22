"use client";

import AppShell from "@/components/layout/AppShell";
import ModelComparisonPage from "@/components/features/comparison/ModelComparisonPage";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function CompareModelsRoutePage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <ModelComparisonPage />
    </AppShell>
  );
}
