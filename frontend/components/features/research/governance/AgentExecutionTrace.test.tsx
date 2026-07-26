import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import AgentExecutionTrace from "@/components/features/research/governance/AgentExecutionTrace";
import type { AgentTraceEvent } from "@/types/researchAgent";

const SAMPLE: AgentTraceEvent[] = [
  {
    id: "evt-0002",
    sequence: 2,
    step: 2,
    node: "review_evidence",
    event: "reviewed",
    label: "LLM evidence interpretation",
    authority: "llm",
    status: "unavailable",
    summary: "LLM interpretation unavailable (deterministic path continues).",
  },
  {
    id: "evt-0001",
    sequence: 1,
    step: 1,
    node: "plan_tool_calls",
    event: "planned",
    label: "Planned deterministic tools",
    authority: "deterministic",
    status: "completed",
    summary: "tools=1",
  },
  {
    id: "evt-0003",
    sequence: 3,
    step: 3,
    node: "prepare_decision_review",
    event: "prepared",
    label: "Prepared decision review",
    authority: "deterministic",
    status: "completed",
    summary: "Deterministic suggestion: Hold",
  },
];

describe("AgentExecutionTrace", () => {
  it("is collapsed by default and sorts by sequence when opened", () => {
    render(<AgentExecutionTrace events={SAMPLE} language="en" />);
    const details = document.querySelector("details.agent-execution-trace");
    expect(details).toBeTruthy();
    expect(details).not.toHaveAttribute("open");
    expect(screen.getByText(/Execution trace/i)).toBeInTheDocument();

    const items = document.querySelectorAll(".agent-execution-trace__item");
    expect(items[0]).toHaveAttribute("data-authority", "deterministic");
    expect(items[1]).toHaveAttribute("data-status", "unavailable");
    expect(items[1].textContent).toMatch(/unavailable/i);
    expect(items[1].textContent).not.toMatch(/workflow failure/i);
  });

  it("keeps human and deterministic labels distinct in Chinese", () => {
    render(
      <AgentExecutionTrace
        language="zh"
        defaultOpen
        events={[
          {
            step: 1,
            sequence: 1,
            node: "await_human_decision",
            event: "waiting",
            authority: "human",
            status: "blocked",
            label: "Waiting for human decision",
            summary: "人工决策待确认",
          },
        ]}
      />
    );
    expect(screen.getByText("人工")).toBeInTheDocument();
    expect(screen.getByText("待批准")).toBeInTheDocument();
  });
});
