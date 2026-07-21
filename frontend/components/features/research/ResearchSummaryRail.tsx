"use client";

import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import {
  buildResearchProtocolParts,
  parseMaWindows,
} from "@/lib/researchProtocol";
import {
  benchmarkLabel,
  researchStatusLabel,
} from "@/lib/researchDisplay";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult } from "@/types/researchExecution";

function formatDate(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function deriveExperimentLabel(
  research: ResearchDetail,
  execution: ResearchExecutionResult | null,
  language: Language,
  notConfiguredLabel: string
): string {
  const parts = buildResearchProtocolParts(research, execution, language);
  const windows = parseMaWindows(research, execution);
  if (
    parts.symbol &&
    typeof windows.shortWindow === "number" &&
    typeof windows.longWindow === "number"
  ) {
    return `${parts.symbol} MA${windows.shortWindow}/${windows.longWindow}`;
  }
  const strategy = research.configuration.strategyName?.trim();
  if (strategy && strategy !== "Not configured" && strategy !== "未配置") {
    return strategy;
  }
  if (research.experimentCount > 0) {
    return language === "zh"
      ? `${research.experimentCount} 个实验`
      : `${research.experimentCount} experiments`;
  }
  return notConfiguredLabel;
}

export type ResearchSummaryRailLabels = {
  title: string;
  status: string;
  nextMilestone: string;
  experiment: string;
  benchmark: string;
  updated: string;
  noMilestone: string;
  experimentNotConfigured: string;
};

export type ResearchSummaryRailProps = {
  research: ResearchDetail;
  language: Language;
  execution: ResearchExecutionResult | null;
  nextMilestone: string | null;
  labels: ResearchSummaryRailLabels;
};

/** Desktop sticky summary — facts only, no duplicated narrative. */
export default function ResearchSummaryRail({
  research,
  language,
  execution,
  nextMilestone,
  labels,
}: ResearchSummaryRailProps) {
  const experiment = deriveExperimentLabel(
    research,
    execution,
    language,
    labels.experimentNotConfigured
  );
  const benchmark = benchmarkLabel(research.configuration.benchmark, language);

  return (
    <aside className="research-summary-rail" aria-label={labels.title}>
      <p className="research-summary-rail__eyebrow">{labels.title}</p>

      <div className="research-summary-rail__row">
        <span className="research-summary-rail__label">{labels.status}</span>
        <StatusBadge
          label={researchStatusLabel(research.status, language)}
          variant={researchLifecycleVariant(research.status)}
        />
      </div>

      <div className="research-summary-rail__row research-summary-rail__row--stack">
        <span className="research-summary-rail__label">{labels.nextMilestone}</span>
        <p className="research-summary-rail__value">
          {nextMilestone ?? labels.noMilestone}
        </p>
      </div>

      <dl className="research-summary-rail__facts">
        <div>
          <dt>{labels.experiment}</dt>
          <dd>{experiment}</dd>
        </div>
        <div>
          <dt>{labels.benchmark}</dt>
          <dd>{benchmark}</dd>
        </div>
        <div>
          <dt>{labels.updated}</dt>
          <dd>{formatDate(research.updatedAt, language)}</dd>
        </div>
      </dl>
    </aside>
  );
}
