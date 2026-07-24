import { API_REQUEST_TIMEOUT_MS, requestJson } from "@/lib/apiRequest";
import type {
  AgentResumeAction,
  AgentRunCreateRequest,
  AgentRunDetail,
  AgentRunSummary,
} from "@/types/researchAgent";

const AGENT_BASE = "/api/v1/research/agent";

export function createAgentRun(
  body: AgentRunCreateRequest,
  signal?: AbortSignal
): Promise<AgentRunSummary> {
  return requestJson<AgentRunSummary>(
    `${AGENT_BASE}/runs`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export function getAgentRun(
  agentRunId: string,
  signal?: AbortSignal
): Promise<AgentRunDetail> {
  return requestJson<AgentRunDetail>(
    `${AGENT_BASE}/runs/${encodeURIComponent(agentRunId)}`,
    { method: "GET", signal },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export function resumeAgentRun(
  agentRunId: string,
  action: AgentResumeAction,
  payload: Record<string, unknown> = {},
  signal?: AbortSignal
): Promise<AgentRunDetail> {
  return requestJson<AgentRunDetail>(
    `${AGENT_BASE}/runs/${encodeURIComponent(agentRunId)}/resume`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, payload }),
      signal,
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}

export function cancelAgentRun(
  agentRunId: string,
  signal?: AbortSignal
): Promise<AgentRunDetail> {
  return requestJson<AgentRunDetail>(
    `${AGENT_BASE}/runs/${encodeURIComponent(agentRunId)}/cancel`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      signal,
    },
    { timeoutMs: API_REQUEST_TIMEOUT_MS }
  );
}
