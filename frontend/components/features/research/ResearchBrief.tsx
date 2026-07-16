"use client";

import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import {
  buildResearchProtocolParts,
  formatResearchProtocolLine,
} from "@/lib/researchProtocol";
import {
  ownerLabel,
  researchNameLabel,
  researchQuestionLabel,
  researchStatusLabel,
} from "@/lib/researchDisplay";
import type { ResearchDetail } from "@/types/research";
import type { ResearchExecutionResult } from "@/types/researchExecution";

export type ResearchBriefLabels = {
  owner: string;
  updated: string;
  evidenceStatus: string;
  decisionStatus: string;
  evidenceComplete: string;
  evidenceIncomplete: string;
  evidencePending: string;
  decisionPending: string;
  evaluationCompleted: string;
  evaluationIncomplete: string;
  evaluationBlocked: string;
};

export type ResearchBriefProps = {
  research: ResearchDetail;
  language: Language;
  execution: ResearchExecutionResult | null;
  evidenceStatusValue: string;
  decisionStatusValue: string;
  labels: ResearchBriefLabels;
  showIdentity?: boolean;
};

function formatUpdated(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ResearchBrief({
  research,
  language,
  execution,
  evidenceStatusValue,
  decisionStatusValue,
  labels,
  showIdentity = true,
}: ResearchBriefProps) {
  const protocolParts = buildResearchProtocolParts(research, execution, language);
  const protocolLine = formatResearchProtocolLine(protocolParts, language);

  return (
    <div className="research-brief">
      {showIdentity ? (
        <header className="research-brief__identity">
          <div>
            <h2 className="research-brief__name">
              {researchNameLabel(research.id, research.name, language)}
            </h2>
            <p className="research-brief__question">
              {researchQuestionLabel(research.id, research.researchQuestion, language)}
            </p>
          </div>
          <StatusBadge
            label={researchStatusLabel(research.status, language)}
            variant={researchLifecycleVariant(research.status)}
          />
        </header>
      ) : null}

      {protocolLine ? (
        <p className="research-brief__protocol">{protocolLine}</p>
      ) : null}

      <dl className="research-brief__meta">
        {showIdentity ? (
          <>
            <div>
              <dt>{labels.owner}</dt>
              <dd>{ownerLabel(research.owner, language)}</dd>
            </div>
            <div>
              <dt>{labels.updated}</dt>
              <dd>{formatUpdated(research.updatedAt, language)}</dd>
            </div>
          </>
        ) : null}
        <div>
          <dt>{labels.evidenceStatus}</dt>
          <dd>{evidenceStatusValue}</dd>
        </div>
        <div>
          <dt>{labels.decisionStatus}</dt>
          <dd>{decisionStatusValue}</dd>
        </div>
      </dl>
    </div>
  );
}
