"use client";

import Link from "next/link";
import { useId, useState } from "react";
import Button from "@/components/ui/Button";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import { deriveExperimentLabel } from "@/components/features/research/ResearchSummaryRail";
import type { Language } from "@/lib/i18n";
import {
  benchmarkLabel,
  researchNameLabel,
  researchQuestionLabel,
  researchStatusLabel,
} from "@/lib/researchDisplay";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult } from "@/types/researchExecution";

function formatDate(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export type ResearchWorkspaceHeaderLabels = {
  back: string;
  moreActions: string;
  moreActionsHint: string;
  owner: string;
  created: string;
  updated: string;
  recommendation: string;
  confidence: string;
  tags: string;
  benchmark: string;
  experiment: string;
  experimentNotConfigured: string;
};

export type ResearchWorkspaceHeaderProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchWorkspaceHeaderLabels;
  execution?: ResearchExecutionResult | null;
};

/** Compact research hero — title, question, status, thin metadata. */
export default function ResearchWorkspaceHeader({
  research,
  language,
  labels,
  execution = null,
}: ResearchWorkspaceHeaderProps) {
  const menuId = useId();
  const [menuOpen, setMenuOpen] = useState(false);
  const experiment = deriveExperimentLabel(
    research,
    execution,
    language,
    labels.experimentNotConfigured
  );

  return (
    <header className="research-hero">
      <div className="research-hero__chrome">
        <Link href="/" className="research-hero__back">
          ← {labels.back}
        </Link>
        <div className="research-hero__menu">
          <Button
            className="btn--ghost"
            aria-expanded={menuOpen}
            aria-controls={menuId}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {labels.moreActions}
          </Button>
          {menuOpen ? (
            <div
              id={menuId}
              className="research-hero__menu-panel"
              role="menu"
            >
              <p className="section-meta">{labels.moreActionsHint}</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="research-hero__body">
        <div className="research-hero__identity">
          <div className="research-hero__title-row">
            <h1 className="research-hero__title">
              {researchNameLabel(research.id, research.name, language)}
            </h1>
            <StatusBadge
              label={researchStatusLabel(research.status, language)}
              variant={researchLifecycleVariant(research.status)}
            />
          </div>
          <p className="research-hero__question">
            {researchQuestionLabel(research.id, research.researchQuestion, language)}
          </p>
        </div>

        <dl className="research-hero__meta">
          <div>
            <dt>{labels.updated}</dt>
            <dd>{formatDate(research.updatedAt, language)}</dd>
          </div>
          <div>
            <dt>{labels.benchmark}</dt>
            <dd>{benchmarkLabel(research.configuration.benchmark, language)}</dd>
          </div>
          <div>
            <dt>{labels.experiment}</dt>
            <dd>{experiment}</dd>
          </div>
        </dl>
      </div>
    </header>
  );
}
