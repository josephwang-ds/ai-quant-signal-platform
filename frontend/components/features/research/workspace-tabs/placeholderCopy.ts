import type { TranslationKey } from "@/lib/i18n";

export type PlaceholderCopy = {
  titleKey: TranslationKey;
  summaryKey: TranslationKey;
  capabilityKeys: TranslationKey[];
};

export const PLACEHOLDER_COPY: Record<"archive" | "files" | "settings", PlaceholderCopy> = {
  archive: {
    titleKey: "researchWsArchiveTitle",
    summaryKey: "researchWsArchiveSummary",
    capabilityKeys: [
      "researchWsArchiveCap1",
      "researchWsArchiveCap2",
      "researchWsArchiveCap3",
    ],
  },
  files: {
    titleKey: "researchWsFilesTitle",
    summaryKey: "researchWsFilesSummary",
    capabilityKeys: [
      "researchWsFilesCap1",
      "researchWsFilesCap2",
      "researchWsFilesCap3",
    ],
  },
  settings: {
    titleKey: "researchWsSettingsTitle",
    summaryKey: "researchWsSettingsSummary",
    capabilityKeys: [
      "researchWsSettingsCap1",
      "researchWsSettingsCap2",
      "researchWsSettingsCap3",
    ],
  },
};
