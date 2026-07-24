export type AgentIntent =
  | "review_definition"
  | "review_readiness"
  | "review_evidence"
  | "prepare_decision";

export type AgentStatus =
  | "running"
  | "awaiting_approval"
  | "completed"
  | "failed"
  | "cancelled";

export type AgentResumeAction =
  | "approve"
  | "edit"
  | "skip"
  | "cancel"
  | "record_decision"
  | "run_additional_validation";

export type AgentRunSummary = {
  agent_run_id: string;
  status: AgentStatus;
  current_node: string;
  summary: string;
};

export type AgentTraceEvent = {
  step: number;
  node: string;
  event: string;
  detail?: string;
  at?: string;
};

export type AgentRunDetail = {
  agent_run_id: string;
  research_id: string;
  intent: AgentIntent;
  status: AgentStatus;
  current_node: string;
  summary: string;
  research_type: string;
  llm_available: boolean;
  llm_provider?: string | null;
  llm_model?: string | null;
  prompt_versions: Record<string, string>;
  graph_version: string;
  evidence_snapshot_id?: string | null;
  knowledge_context: Array<Record<string, unknown>>;
  requested_tools: Array<Record<string, unknown>>;
  tool_results: Array<Record<string, unknown>>;
  definition_review: Record<string, unknown>;
  completeness: Record<string, unknown>;
  ai_interpretation: Record<string, unknown>;
  decision_review: Record<string, unknown>;
  pending_approval: Record<string, unknown>;
  human_decision: Record<string, unknown>;
  missing_evidence: string[];
  recommended_next_steps: string[];
  errors: string[];
  trace: AgentTraceEvent[];
  step_count: number;
  started_at?: string | null;
  completed_at?: string | null;
};

export type AgentRunCreateRequest = {
  research_id: string;
  intent: AgentIntent;
  research_type?: "trend_following" | "factor";
  research_definition?: Record<string, unknown>;
  evidence_snapshot_id?: string | null;
  previous_decisions?: Array<Record<string, unknown>>;
  user_question?: string;
};
