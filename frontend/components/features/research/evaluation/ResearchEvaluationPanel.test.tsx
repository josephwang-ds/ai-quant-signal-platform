import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ResearchEvaluationPanel, {
  type ResearchEvaluationLabels,
} from "@/components/features/research/evaluation/ResearchEvaluationPanel";
import LoadingState from "@/components/ui/LoadingState";
import {
  ResearchEvaluationApiError,
  fetchResearchEvaluation,
} from "@/lib/researchEvaluationApi";
import type { ResearchEvaluationResult } from "@/types/researchEvaluation";

const labels: ResearchEvaluationLabels = {
  title: "Evaluation",
  summary: "Evaluation summarizes calculated validation evidence only.",
  status: "Evaluation status",
  completed: "Completed",
  incomplete: "Incomplete",
  blocked: "Blocked",
  source: "Source",
  generated: "Generated",
  coverageTitle: "Evidence coverage",
  implementedStages: "Implemented stages",
  completedStagesCount: "Completed stages",
  coveragePercentage: "Coverage",
  coverageDisclaimer:
    "Coverage measures implementation completeness only. It is not a confidence, quality, or robustness score.",
  evidenceSummaryTitle: "Evidence summary",
  stageColumn: "Stage",
  statusColumn: "Status",
  summaryColumn: "Summary",
  completedEvidenceTitle: "Completed evidence",
  incompleteEvidenceTitle: "Incomplete evidence",
  outstandingEvidenceTitle: "Outstanding evidence",
  limitationsTitle: "Limitations",
  blockersTitle: "Blockers",
  decisionReadinessTitle: "Decision readiness",
  keyFindingsTitle: "Key findings",
  nextGovernanceActionTitle: "Next governance action",
  detailsTitle: "Evaluation details",
  none: "None",
  notAvailable: "n/a",
};

function buildEvaluation(
  overrides: Partial<ResearchEvaluationResult> = {}
): ResearchEvaluationResult {
  return {
    research_id: "ma-crossover-spy",
    evaluation_status: "incomplete",
    evidence_summary: [
      {
        stage: "historical_backtest",
        label: "Historical backtest",
        status: "completed",
        summary: "Full-history deterministic MA-crossover evidence was calculated.",
      },
      {
        stage: "out_of_sample",
        label: "Out-of-sample validation",
        status: "incomplete",
        summary: "Chronological OOS evidence is incomplete.",
      },
    ],
    evidence_coverage: {
      implemented_stage_count: 6,
      completed_stage_count: 5,
      coverage_percentage: 83.33,
    },
    completed_stages: ["Historical backtest", "Benchmark comparison"],
    incomplete_stages: ["Out-of-sample validation"],
    unavailable_stages: [
      "Stress testing",
      "Regime analysis",
      "Walk-forward validation",
      "Monte Carlo simulation",
    ],
    blockers: ["Insufficient OOS history: need at least 252 valid return rows; got 150."],
    limitations: [
      "Evaluation is based on historical evidence only; it performs no new calculations.",
      "Stress testing is not implemented.",
      "Paper trading is unavailable.",
    ],
    outstanding_evidence: [
      "Stress testing",
      "Regime analysis",
      "Walk-forward validation",
      "Monte Carlo simulation",
      "Paper trading",
    ],
    provenance: {
      research_id: "ma-crossover-spy",
      validation_run_id: "val-sample-run-id",
      validation_generated_at: "2026-07-14T01:02:00Z",
      market_data_provenance: {
        provider: "yahoo",
        source: "Yahoo Finance via yfinance",
      },
    },
    generated_at: "2026-07-14T01:03:00Z",
    ...overrides,
  };
}

describe("ResearchEvaluationPanel", () => {
  it("shows review summary before collapsed evaluation details", () => {
    const { container } = render(
      <ResearchEvaluationPanel evaluation={buildEvaluation()} labels={labels} language="en" />
    );

    expect(screen.getByText("Key findings")).toBeInTheDocument();
    expect(
      screen.getByText("Full-history deterministic MA-crossover evidence was calculated.")
    ).toBeInTheDocument();
    const details = container.querySelector("details.validation-evidence-disclosure");
    expect(details).toBeTruthy();
    expect((details as HTMLDetailsElement).open).toBe(false);
  });

  it("shows evaluation status, coverage, and evidence summary from backend evidence", () => {
    render(
      <ResearchEvaluationPanel evaluation={buildEvaluation()} labels={labels} language="en" />
    );

    expect(screen.getAllByText("Incomplete").length).toBeGreaterThan(0);
    expect(screen.getAllByText("83.33%").length).toBeGreaterThan(0);
  });

  it("lists completed, incomplete, outstanding evidence, limitations, and blockers", () => {
    render(
      <ResearchEvaluationPanel evaluation={buildEvaluation()} labels={labels} language="en" />
    );

    expect(screen.getByText("Benchmark comparison")).toBeInTheDocument();
    expect(screen.getByText("Monte Carlo simulation")).toBeInTheDocument();
    expect(screen.getByText("Stress testing is not implemented.")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Insufficient OOS history: need at least 252 valid return rows; got 150."
      ).length
    ).toBeGreaterThan(0);
  });

  it("never renders a confidence score, star rating, or buy/sell recommendation", () => {
    render(
      <ResearchEvaluationPanel evaluation={buildEvaluation()} labels={labels} language="en" />
    );

    expect(screen.queryByText(/confidence score/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^confidence$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/recommend/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/★/)).not.toBeInTheDocument();
    expect(screen.queryByText(/^buy$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^sell$/i)).not.toBeInTheDocument();
  });

  it("renders a blocked evaluation without treating it as a strategy failure", () => {
    render(
      <ResearchEvaluationPanel
        evaluation={buildEvaluation({
          evaluation_status: "blocked",
          blockers: ["Provider unavailable: provider unavailable"],
          completed_stages: [],
          incomplete_stages: [
            "Historical backtest",
            "Benchmark comparison",
            "Out-of-sample validation",
            "Parameter sensitivity",
            "Transaction-cost sensitivity",
            "Data quality",
          ],
          evidence_summary: [],
          evidence_coverage: {
            implemented_stage_count: 6,
            completed_stage_count: 0,
            coverage_percentage: 0,
          },
        })}
        labels={labels}
        language="en"
      />
    );

    expect(screen.getAllByText("Blocked").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Provider unavailable: provider unavailable").length
    ).toBeGreaterThan(0);
    expect(screen.queryByText(/failed strategy/i)).not.toBeInTheDocument();
  });

  it("shows a loading state without a fabricated status", () => {
    render(<LoadingState message="Loading evaluation evidence from backend…" />);
    expect(
      screen.getByText("Loading evaluation evidence from backend…")
    ).toBeInTheDocument();
    expect(screen.queryByText("Completed")).not.toBeInTheDocument();
  });
});

describe("researchEvaluationApi", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the evaluation endpoint and returns backend success", async () => {
    const evaluation = buildEvaluation();
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => evaluation,
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchResearchEvaluation("val-sample-run-id")).resolves.toEqual(
      evaluation
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/research/evaluation",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          research_id: "ma-crossover-spy",
          validation_run_id: "val-sample-run-id",
        }),
      })
    );
  });

  it("surfaces backend errors without fallback evidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 400,
        json: async () => ({ detail: "Unsupported research_id 'unknown'." }),
      }))
    );

    await expect(
      fetchResearchEvaluation("val-sample-run-id")
    ).rejects.toBeInstanceOf(ResearchEvaluationApiError);
    await expect(fetchResearchEvaluation("val-sample-run-id")).rejects.toMatchObject({
      status: 400,
      message: "Unsupported research_id 'unknown'.",
    });
  });

  it("surfaces a 404 when the validation_run_id is unknown to the backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 404,
        json: async () => ({
          detail: "Unknown validation_run_id 'val-missing'.",
        }),
      }))
    );

    await expect(fetchResearchEvaluation("val-missing")).rejects.toMatchObject({
      status: 404,
      message: "Unknown validation_run_id 'val-missing'.",
    });
  });
});
