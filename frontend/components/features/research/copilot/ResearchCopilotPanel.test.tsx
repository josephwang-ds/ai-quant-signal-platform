import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ResearchCopilotPanel from "@/components/features/research/copilot/ResearchCopilotPanel";

const labels = {
  title: "Evidence-Grounded Research Copilot",
  subtitle: "Explains existing workspace evidence.",
  disclaimer: "Answers are interpretation only.",
  sampleQuestionsTitle: "Sample questions",
  questionPlaceholder: "Ask about evidence",
  askButton: "Ask Copilot",
  askingButton: "Generating grounded answer…",
  answerTitle: "Answer",
  citationsTitle: "Evidence citations",
  warningsTitle: "Warnings",
  groundingTitle: "Grounding status",
  generatedAt: "Generated at",
  grounded: "Grounded",
  partiallyGrounded: "Partially grounded",
  unavailable: "Unavailable",
  awaitingValidationTitle: "Validation evidence required",
  awaitingValidationDescription: "Run validation first.",
  goToValidation: "Go to Validation",
  notConfigured: "Research Copilot is not configured for this deployment.",
  limitations: "The Copilot cannot approve strategies or predict returns.",
  factorSummaryTitle: "Factor evidence summary",
  factorRankIc: "RankIC",
  factorIcir: "ICIR",
  factorTurnover: "Turnover",
  factorLongShort: "Long–short return",
  factorStability: "Stability",
  factorWarnings: "Warnings",
};

describe("ResearchCopilotPanel", () => {
  it("shows awaiting validation guidance", () => {
    render(
      <ResearchCopilotPanel
        labels={labels}
        sampleQuestions={["Why is evaluation incomplete?"]}
        status="awaiting_validation"
        result={null}
        error={null}
        question=""
        onQuestionChange={vi.fn()}
        onAsk={vi.fn()}
        onSampleQuestion={vi.fn()}
      />
    );

    expect(screen.getByText(labels.title)).toBeInTheDocument();
    expect(screen.getByText(labels.awaitingValidationTitle)).toBeInTheDocument();
    expect(screen.queryByText(/buy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sell/i)).not.toBeInTheDocument();
  });

  it("renders grounded answer, citations, and disclaimer", () => {
    render(
      <ResearchCopilotPanel
        labels={labels}
        sampleQuestions={["Why is evaluation incomplete?"]}
        status="ready"
        result={{
          research_id: "ma-crossover-spy",
          answer: "Stress testing evidence is still outstanding.",
          citations: [
            {
              source_type: "evaluation",
              source_id: "val-1",
              label: "Outstanding evidence",
              excerpt: "Stress testing unavailable.",
            },
          ],
          warnings: [
            {
              code: "partial_context",
              message: "Some documentation chunks were truncated.",
            },
          ],
          grounding_status: "partially_grounded",
          model: "fake-copilot-v1",
          generated_at: "2026-07-15T00:00:00Z",
        }}
        error={null}
        question="Why incomplete?"
        onQuestionChange={vi.fn()}
        onAsk={vi.fn()}
        onSampleQuestion={vi.fn()}
      />
    );

    expect(screen.getByText(labels.partiallyGrounded)).toBeInTheDocument();
    expect(screen.getByText(/Stress testing evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Outstanding evidence/i)).toBeInTheDocument();
    expect(screen.getByText(labels.limitations)).toBeInTheDocument();
  });

  it("renders structured factor evidence summary without trade CTAs", () => {
    render(
      <ResearchCopilotPanel
        labels={labels}
        sampleQuestions={["What does the RankIC evidence show?"]}
        status="ready"
        result={{
          research_id: "cross-sectional-factor-sector-etfs",
          answer:
            "Factor validation evidence summary (historical research only).",
          citations: [
            {
              source_type: "factor_validation",
              source_id: "val-factor-1",
              label: "RankIC summary",
              excerpt: "mean_rank_ic=0.12",
            },
          ],
          warnings: [],
          grounding_status: "grounded",
          model: "fake-copilot-v1",
          generated_at: "2026-07-15T00:00:00Z",
          factor_summary: {
            rank_ic: "0.12",
            icir: "0.8",
            turnover: "0.42",
            long_short_return: "0.15",
            stability: "RankIC sign consistent in both halves.",
            warnings: ["demo_synthetic_universe"],
            citation_ids: ["factor:rank_ic"],
          },
        }}
        error={null}
        question="What does the RankIC evidence show?"
        onQuestionChange={vi.fn()}
        onAsk={vi.fn()}
        onSampleQuestion={vi.fn()}
      />
    );

    expect(screen.getByText(labels.factorSummaryTitle)).toBeInTheDocument();
    expect(screen.getByText("0.12")).toBeInTheDocument();
    expect(screen.getByText("0.8")).toBeInTheDocument();
    expect(screen.getByText("0.42")).toBeInTheDocument();
    expect(screen.getByText("0.15")).toBeInTheDocument();
    expect(screen.queryByText(/buy/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sell/i)).not.toBeInTheDocument();
  });

  it("shows honest unavailable state without a fake answer", () => {
    render(
      <ResearchCopilotPanel
        labels={labels}
        sampleQuestions={[]}
        status="error"
        result={null}
        error={labels.notConfigured}
        question="test"
        onQuestionChange={vi.fn()}
        onAsk={vi.fn()}
        onSampleQuestion={vi.fn()}
      />
    );

    expect(screen.getByText(labels.notConfigured)).toBeInTheDocument();
    expect(screen.queryByText(/guaranteed profit/i)).not.toBeInTheDocument();
  });

  it("fires sample question selection", () => {
    const onSampleQuestion = vi.fn();
    render(
      <ResearchCopilotPanel
        labels={labels}
        sampleQuestions={["How sensitive is this strategy to transaction costs?"]}
        status="idle"
        result={null}
        error={null}
        question=""
        onQuestionChange={vi.fn()}
        onAsk={vi.fn()}
        onSampleQuestion={onSampleQuestion}
      />
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "How sensitive is this strategy to transaction costs?",
      })
    );
    expect(onSampleQuestion).toHaveBeenCalledWith(
      "How sensitive is this strategy to transaction costs?"
    );
  });
});
