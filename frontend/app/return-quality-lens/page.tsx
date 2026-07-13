"use client";

import AppShell from "@/components/layout/AppShell";
import SectionCard from "@/components/ui/SectionCard";
import ReturnQualityLens from "@/components/features/executive/ReturnQualityLens";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function ReturnQualityLensPage() {
  const { language, setLanguage } = useWorkspaceLanguage();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <ReturnQualityLens showModuleLink={false} />
      </SectionCard>
    </AppShell>
  );
}
