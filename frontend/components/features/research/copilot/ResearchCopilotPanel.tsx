"use client";

import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import LoadingState from "@/components/ui/LoadingState";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import type { ResearchCopilotResult } from "@/types/researchCopilot";

export type ResearchCopilotLabels = {
  title: string;
  subtitle: string;
  disclaimer: string;
  sampleQuestionsTitle: string;
  questionPlaceholder: string;
  askButton: string;
  askingButton: string;
  answerTitle: string;
  citationsTitle: string;
  warningsTitle: string;
  groundingTitle: string;
  generatedAt: string;
  grounded: string;
  partiallyGrounded: string;
  unavailable: string;
  awaitingValidationTitle: string;
  awaitingValidationDescription: string;
  goToValidation: string;
  notConfigured: string;
  limitations: string;
};

type Props = {
  labels: ResearchCopilotLabels;
  sampleQuestions: string[];
  status: "idle" | "awaiting_validation" | "loading" | "ready" | "error";
  result: ResearchCopilotResult | null;
  error: string | null;
  question: string;
  onQuestionChange: (value: string) => void;
  onAsk: () => void;
  onSampleQuestion: (value: string) => void;
  onGoToValidation?: () => void;
};

function groundingVariant(status: string): "success" | "warning" | "danger" {
  if (status === "grounded") return "success";
  if (status === "partially_grounded") return "warning";
  return "danger";
}

export default function ResearchCopilotPanel({
  labels,
  sampleQuestions,
  status,
  result,
  error,
  question,
  onQuestionChange,
  onAsk,
  onSampleQuestion,
  onGoToValidation,
}: Props) {
  return (
    <div className="research-copilot">
      <SectionCard>
        <SectionHeader title={labels.title} description={labels.subtitle} />
        <p className="section-meta research-copilot__disclaimer">{labels.disclaimer}</p>
      </SectionCard>

      {status === "awaiting_validation" ? (
        <SectionCard>
          <h3>{labels.awaitingValidationTitle}</h3>
          <p className="section-meta">{labels.awaitingValidationDescription}</p>
          {onGoToValidation ? (
            <Button type="button" onClick={onGoToValidation}>
              {labels.goToValidation}
            </Button>
          ) : null}
        </SectionCard>
      ) : null}

      {status !== "awaiting_validation" ? (
        <>
          <SectionCard>
            <h3>{labels.sampleQuestionsTitle}</h3>
            <div className="research-copilot__samples">
              {sampleQuestions.map((sample) => (
                <button
                  key={sample}
                  type="button"
                  className="research-copilot__sample"
                  onClick={() => onSampleQuestion(sample)}
                >
                  {sample}
                </button>
              ))}
            </div>
            <label className="research-copilot__field">
              <span className="section-meta">{labels.questionPlaceholder}</span>
              <textarea
                className="research-copilot__input"
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
                rows={4}
                maxLength={1000}
              />
            </label>
            <Button
              type="button"
              onClick={onAsk}
              disabled={status === "loading" || !question.trim()}
            >
              {status === "loading" ? labels.askingButton : labels.askButton}
            </Button>
          </SectionCard>

          {status === "loading" ? <LoadingState message={labels.askingButton} /> : null}
          {error ? <ErrorAlert message={error} /> : null}

          {result ? (
            <>
              <SectionCard>
                <div className="research-copilot__meta">
                  <span className="section-meta">{labels.groundingTitle}</span>
                  <StatusBadge
                    label={
                      result.grounding_status === "grounded"
                        ? labels.grounded
                        : result.grounding_status === "partially_grounded"
                          ? labels.partiallyGrounded
                          : labels.unavailable
                    }
                    variant={groundingVariant(result.grounding_status)}
                  />
                  <span className="section-meta">
                    {labels.generatedAt}: {result.generated_at}
                  </span>
                </div>
                <h3>{labels.answerTitle}</h3>
                <p className="research-copilot__answer">{result.answer}</p>
                <p className="section-meta">{labels.limitations}</p>
              </SectionCard>

              <SectionCard>
                <h3>{labels.citationsTitle}</h3>
                <ul className="research-copilot__citations">
                  {result.citations.map((citation) => (
                    <li key={`${citation.source_type}-${citation.source_id}-${citation.label}`}>
                      <strong>
                        {citation.label} ({citation.source_type})
                      </strong>
                      <p className="section-meta">{citation.excerpt}</p>
                    </li>
                  ))}
                </ul>
              </SectionCard>

              {result.warnings.length > 0 ? (
                <SectionCard>
                  <h3>{labels.warningsTitle}</h3>
                  <ul className="research-copilot__warnings">
                    {result.warnings.map((warning) => (
                      <li key={warning.code}>{warning.message}</li>
                    ))}
                  </ul>
                </SectionCard>
              ) : null}
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
