"use client";

import Button from "@/components/ui/Button";
import type { Language } from "@/lib/i18n";
import {
  formatResearchProtocolLine,
  buildResearchProtocolParts,
} from "@/lib/researchProtocol";
import { researchQuestionLabel } from "@/lib/researchDisplay";
import {
  workflowStepToSection,
  type WorkflowStepId,
  type WorkflowStepState,
} from "@/lib/researchWorkflow";
import type {
  ResearchDetail,
  ResearchWorkspaceSection,
} from "@/types/research";
import type { ResearchExecutionResult } from "@/types/researchExecution";

type ActionCopy = {
  title: string;
  description: string;
  cta: string;
};

export type ResearchMissionPanelLabels = {
  eyebrow: string;
  title: string;
  question: string;
  method: string;
  protocol: string;
  protocolUnavailable: string;
  now: string;
  guardrail: string;
  methodSteps: [string, string, string, string, string];
  actions: Record<WorkflowStepId, ActionCopy>;
  runningResearch: string;
  retryResearch: string;
};

export type ResearchMissionPanelProps = {
  research: ResearchDetail;
  execution: ResearchExecutionResult | null;
  language: Language;
  primaryStep: WorkflowStepId;
  primaryState: WorkflowStepState;
  labels: ResearchMissionPanelLabels;
  onRunResearch: () => void;
  onRunValidation: () => void;
  onOpenSection: (section: ResearchWorkspaceSection) => void;
};

export default function ResearchMissionPanel({
  research,
  execution,
  language,
  primaryStep,
  primaryState,
  labels,
  onRunResearch,
  onRunValidation,
  onOpenSection,
}: ResearchMissionPanelProps) {
  const protocol = formatResearchProtocolLine(
    buildResearchProtocolParts(research, execution, language),
    language
  );
  const action = labels.actions[primaryStep];
  const isLoading = primaryState === "loading";
  const isFailed = primaryState === "failed";

  const handleAction = () => {
    if (primaryStep === "research") {
      onRunResearch();
      return;
    }
    if (primaryStep === "validation") {
      onRunValidation();
      return;
    }
    onOpenSection(workflowStepToSection(primaryStep));
  };

  const cta =
    primaryStep === "research" && isLoading
      ? labels.runningResearch
      : primaryStep === "research" && isFailed
        ? labels.retryResearch
        : action.cta;

  return (
    <section className="research-mission" aria-labelledby="research-mission-title">
      <header className="research-mission__header">
        <p className="research-mission__eyebrow">{labels.eyebrow}</p>
        <h2 id="research-mission-title">{labels.title}</h2>
      </header>

      <article className="research-mission__question">
        <span>{labels.question}</span>
        <h3>
          {researchQuestionLabel(
            research.id,
            research.researchQuestion,
            language
          )}
        </h3>
        <p>{labels.guardrail}</p>
      </article>

      <article className="research-mission__method">
        <div>
          <span>{labels.method}</span>
          <p>
            <strong>{labels.protocol}</strong>{" "}
            {protocol ?? labels.protocolUnavailable}
          </p>
        </div>
        <ol>
          {labels.methodSteps.map((step, index) => (
            <li key={step}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              {step}
            </li>
          ))}
        </ol>
      </article>

      <article className="research-mission__action">
        <span>{labels.now}</span>
        <h3>{action.title}</h3>
        <p>{action.description}</p>
        <Button primary disabled={isLoading} onClick={handleAction}>
          {cta}
        </Button>
      </article>
    </section>
  );
}
