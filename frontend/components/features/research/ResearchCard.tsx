"use client";

import Link from "next/link";
import Button from "@/components/ui/Button";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import {
  evidenceStatusLabel,
  parameterLineLabel,
  researchNameLabel,
  researchQuestionLabel,
  researchStatusLabel,
  strategyLabel,
} from "@/lib/researchDisplay";
import { deriveResearchListNextStep } from "@/lib/researchWorkflow";
import type { ResearchListItem } from "@/types/research";

function formatUpdated(value: string, language: Language): string {
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

export type ResearchCardProps = {
  item: ResearchListItem;
  language: Language;
  labels: {
    openWorkspace: string;
    archive: string;
    experiments: string;
    updated: string;
    symbol: string;
    strategy: string;
    evidenceStatus: string;
    nextStep: string;
    nextStepRunResearch: string;
    nextStepValidate: string;
    nextStepEvaluate: string;
    nextStepReview: string;
    more: string;
  };
  onArchive: (id: string) => void;
};

/**
 * Slim Research List card — identity + lifecycle signals only.
 * Detail metrics live inside the Research Workspace.
 */
export default function ResearchCard({
  item,
  language,
  labels,
  onArchive,
}: ResearchCardProps) {
  const nextStep = deriveResearchListNextStep(
    item.integrity.validationStatus,
    item.integrity.evaluationStatus,
    {
      runResearch: labels.nextStepRunResearch,
      validate: labels.nextStepValidate,
      evaluate: labels.nextStepEvaluate,
      review: labels.nextStepReview,
    }
  );

  return (
    <article className="research-card research-card--slim">
      <header className="research-card__header">
        <div className="research-card__title-block">
          <h2 className="research-card__name">{researchNameLabel(item.id, item.name, language)}</h2>
          <StatusBadge
            label={researchStatusLabel(item.status, language)}
            variant={researchLifecycleVariant(item.status)}
          />
        </div>
      </header>

      <p className="research-card__question">
        {researchQuestionLabel(item.id, item.researchQuestion, language)}
      </p>

      <dl className="research-card__meta research-card__meta--slim">
        <div className="research-card__meta-item">
          <dt>{labels.symbol}</dt>
          <dd className="font-mono">{item.configuration.symbol}</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.strategy}</dt>
          <dd>
            {strategyLabel(item.configuration.strategyName, language)}
            {item.configuration.parameterLines.length > 0 ? (
              <span className="research-card__strategy-params">
                {item.configuration.parameterLines
                  .slice(0, 2)
                  .map((line) => parameterLineLabel(line, language))
                  .join(" · ")}
              </span>
            ) : null}
          </dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.experiments}</dt>
          <dd className="font-mono">{item.experimentCount}</dd>
        </div>
        <div className="research-card__meta-item">
          <dt>{labels.updated}</dt>
          <dd>{formatUpdated(item.updatedAt, language)}</dd>
        </div>
        <div className="research-card__meta-item research-card__meta-item--wide">
          <dt>{labels.evidenceStatus}</dt>
          <dd>{evidenceStatusLabel(item.integrity.validationStatus, language)}</dd>
        </div>
        <div className="research-card__meta-item research-card__meta-item--wide">
          <dt>{labels.nextStep}</dt>
          <dd>{nextStep}</dd>
        </div>
      </dl>

      <footer className="research-card__actions">
        <Link
          href={`/research/${encodeURIComponent(item.id)}`}
          className="btn btn--primary"
        >
          {labels.openWorkspace}
        </Link>
        <details className="research-card__overflow">
          <summary aria-label={labels.more} title={labels.more}>•••</summary>
          <div className="research-card__overflow-menu">
            <Button
              onClick={() => onArchive(item.id)}
              disabled={item.status === "Archived"}
              className="btn--ghost"
            >
              {labels.archive}
            </Button>
          </div>
        </details>
      </footer>
    </article>
  );
}
