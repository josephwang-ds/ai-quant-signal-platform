"use client";

import { useCallback, useEffect, useState } from "react";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  fetchResearchEvaluation,
  ResearchEvaluationApiError,
} from "@/lib/researchEvaluationApi";
import type {
  ResearchEvaluationRequestStatus,
  ResearchEvaluationResult,
} from "@/types/researchEvaluation";

/**
 * Evaluation never triggers its own Validation run. It only summarizes a
 * ValidationResult already saved by a prior Validation request, identified
 * by validationRunId. When validationRunId is not yet available, the hook
 * reports "awaiting_validation" and performs no request — it never falls
 * back to mock evidence and never silently runs Validation itself.
 */
export function useResearchEvaluation(
  researchId: string,
  enabled: boolean,
  validationRunId: string | null
) {
  const requestEnabled = enabled && researchId === CANONICAL_RESEARCH_ID;
  const [status, setStatus] = useState<ResearchEvaluationRequestStatus>("idle");
  const [evaluation, setEvaluation] =
    useState<ResearchEvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  useEffect(() => {
    if (!requestEnabled) {
      setStatus("idle");
      setEvaluation(null);
      setError(null);
      return;
    }

    if (!validationRunId) {
      setStatus("awaiting_validation");
      setEvaluation(null);
      setError(null);
      return;
    }

    const controller = new AbortController();
    setStatus("loading");
    setEvaluation(null);
    setError(null);

    void (async () => {
      try {
        const result = await fetchResearchEvaluation(validationRunId, {
          signal: controller.signal,
        });
        if (!controller.signal.aborted) {
          setEvaluation(result);
          setStatus("ready");
        }
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }
        setEvaluation(null);
        setStatus("error");
        setError(
          err instanceof ResearchEvaluationApiError
            ? err.message
            : "Research evaluation unavailable. No score is fabricated."
        );
      }
    })();

    return () => controller.abort();
  }, [requestEnabled, validationRunId, reloadToken]);

  return {
    enabled: requestEnabled,
    status,
    evaluation,
    error,
    reload,
  };
}
