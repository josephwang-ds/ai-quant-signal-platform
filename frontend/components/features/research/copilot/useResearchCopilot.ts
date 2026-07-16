"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiRequestError, getApiUserMessage } from "@/lib/apiRequest";
import { fetchResearchCopilot } from "@/lib/researchCopilotApi";
import type {
  ResearchCopilotRequestStatus,
  ResearchCopilotResult,
} from "@/types/researchCopilot";

export function useResearchCopilot(
  researchId: string,
  enabled: boolean,
  validationRunId: string | null
) {
  const requestEnabled = enabled;
  const [status, setStatus] = useState<ResearchCopilotRequestStatus>("idle");
  const [result, setResult] = useState<ResearchCopilotResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);

  useEffect(() => {
    if (!requestEnabled) {
      setStatus("idle");
      setResult(null);
      setError(null);
      setLastQuestion(null);
      return;
    }
    if (!validationRunId) {
      setStatus("awaiting_validation");
      setResult(null);
      setError(null);
      return;
    }
    setStatus((previous) =>
      previous === "awaiting_validation" ? "idle" : previous
    );
  }, [requestEnabled, validationRunId]);

  const ask = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!requestEnabled) {
        return;
      }
      if (!validationRunId) {
        setStatus("awaiting_validation");
        setResult(null);
        setError(null);
        return;
      }
      if (!trimmed) {
        return;
      }

      setStatus("loading");
      setResult(null);
      setError(null);
      setLastQuestion(trimmed);

      try {
        const response = await fetchResearchCopilot(validationRunId, trimmed, {
          researchId,
        });
        setResult(response);
        setStatus("ready");
      } catch (err) {
        setResult(null);
        setStatus("error");
        setError(
          err instanceof ApiRequestError && err.backendDetail
            ? err.backendDetail
            : getApiUserMessage(
                err,
                "Research Copilot is unavailable. No generated answer was fabricated."
              )
        );
      }
    },
    [requestEnabled, researchId, validationRunId]
  );

  const reset = useCallback(() => {
    if (!requestEnabled) {
      setStatus("idle");
      setResult(null);
      setError(null);
      setLastQuestion(null);
      return;
    }
    if (!validationRunId) {
      setStatus("awaiting_validation");
      setResult(null);
      setError(null);
      setLastQuestion(null);
      return;
    }
    setStatus("idle");
    setResult(null);
    setError(null);
    setLastQuestion(null);
  }, [requestEnabled, validationRunId]);

  return {
    enabled: requestEnabled,
    status,
    result,
    error,
    lastQuestion,
    ask,
    reset,
  };
}
