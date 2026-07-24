"use client";

import AppShell from "@/components/layout/AppShell";
import FeatureInterpretationPage from "@/components/features/comparison/FeatureInterpretationPage";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function FeatureInterpretationRoutePage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <FeatureInterpretationPage />
    </AppShell>
  );
}
