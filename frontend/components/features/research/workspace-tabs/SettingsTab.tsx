"use client";

import WorkspacePlaceholder from "@/components/features/research/WorkspacePlaceholder";
import type { TranslationKey } from "@/lib/i18n";
import type { ResearchWorkspaceSection } from "@/types/research";
import { PLACEHOLDER_COPY } from "./placeholderCopy";

export type SettingsTabProps = {
  section: Extract<ResearchWorkspaceSection, "settings" | "files">;
  tr: (key: TranslationKey) => string;
};

export default function SettingsTab({ section, tr }: SettingsTabProps) {
  const copy = PLACEHOLDER_COPY[section];
  return (
    <WorkspacePlaceholder
      title={tr(copy.titleKey)}
      summary={tr(copy.summaryKey)}
      plannedCapabilities={copy.capabilityKeys.map((key) => tr(key))}
      deferredNote={tr("researchWsDeferredNote")}
      emptyTitle={tr("researchWsDeferredEmptyTitle")}
      capabilitiesCaption={tr("researchWsPlannedCapabilities")}
    />
  );
}
