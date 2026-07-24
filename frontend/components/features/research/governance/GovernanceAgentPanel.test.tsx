import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import GovernanceAgentPanel from "@/components/features/research/governance/GovernanceAgentPanel";
import type { ResearchDetail } from "@/types/research";

vi.mock("@/lib/researchAgentApi", () => ({
  createAgentRun: vi.fn(async () => ({
    agent_run_id: "agent-test",
    status: "awaiting_approval",
    current_node: "request_tool_approval",
    summary: "Awaiting approval",
  })),
  getAgentRun: vi.fn(async () => ({
    agent_run_id: "agent-test",
    research_id: "ma-crossover-spy",
    intent: "review_evidence",
    status: "awaiting_approval",
    current_node: "request_tool_approval",
    summary: "Awaiting human approval for deterministic tools.",
    research_type: "trend_following",
    llm_available: false,
    prompt_versions: {},
    graph_version: "governance_agent_graph_v1",
    knowledge_context: [
      {
        knowledge_id: "kb.trend_following.v1",
        title: "Trend Following Methodology",
        version: "v1",
        excerpt: "Buy-and-Hold is the primary benchmark.",
      },
    ],
    requested_tools: [],
    tool_results: [],
    definition_review: {},
    completeness: {},
    ai_interpretation: {},
    decision_review: {},
    pending_approval: {
      type: "tool_approval",
      tools: [
        {
          tool_name: "run_oos_validation",
          reason: "OOS missing",
        },
      ],
    },
    human_decision: {},
    missing_evidence: ["oos"],
    recommended_next_steps: [],
    errors: [],
    trace: [
      {
        step: 1,
        node: "classify_intent",
        event: "classified",
        detail: "review_evidence",
      },
    ],
  })),
  resumeAgentRun: vi.fn(),
  cancelAgentRun: vi.fn(),
}));

vi.mock("@/lib/researchDecisionRecord", () => ({
  getResearchDecisionRecord: vi.fn(() => null),
}));

const research = {
  id: "ma-crossover-spy",
  name: "MA Crossover",
  researchQuestion: "Does MA beat buy-and-hold?",
  hypothesis: "Trend filter helps historically.",
  configuration: { symbol: "SPY", parameterLines: ["MA20/60"] },
  knownWeaknesses: ["demo"],
  openQuestions: ["Is lag sufficient?"],
} as unknown as ResearchDetail;

describe("GovernanceAgentPanel", () => {
  it("renders disabled-start state and task buttons without trade CTAs", () => {
    render(
      <GovernanceAgentPanel
        research={research}
        isFactorTemplate={false}
        evidenceSnapshotId={null}
        language="en"
      />
    );
    expect(
      screen.getByText("Quant Research Governance Agent")
    ).toBeInTheDocument();
    expect(screen.getByText(/Evidence First/i)).toBeInTheDocument();
    expect(screen.getByText("Review Research Definition")).toBeInTheDocument();
    expect(screen.queryByText(/buy now/i)).not.toBeInTheDocument();
  });

  it("loads a run and shows approval card with knowledge citation", async () => {
    render(
      <GovernanceAgentPanel
        research={research}
        isFactorTemplate={false}
        evidenceSnapshotId="val-1"
        language="en"
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Start Agent workflow/i }));
    expect(await screen.findByText(/Awaiting human approval/i)).toBeInTheDocument();
    expect(screen.getByText("Pending tool approval")).toBeInTheDocument();
    expect(screen.getByText(/kb.trend_following.v1/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Skip" })).toBeInTheDocument();
  });
});
