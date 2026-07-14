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

export function useResearchEvaluation(researchId: string, enabled: boolean) {
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

    const controller = new AbortController();
    setStatus("loading");
    setEvaluation(null);
    setError(null);

    void (async () => {
      try {
        const result = await fetchResearchEvaluation({
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
  }, [requestEnabled, reloadToken]);

  return {
    enabled: requestEnabled,
    status,
    evaluation,
    error,
    reload,
  };
}
