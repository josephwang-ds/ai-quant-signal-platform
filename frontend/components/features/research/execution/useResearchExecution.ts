"use client";

import { useCallback, useEffect, useState } from "react";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import {
  fetchResearchExecution,
  ResearchExecutionApiError,
} from "@/lib/researchExecutionApi";
import type {
  ResearchExecutionResult,
  ResearchExecutionStatus,
} from "@/types/researchExecution";

export function useResearchExecution(researchId: string) {
  const enabled = researchId === CANONICAL_RESEARCH_ID;
  const [status, setStatus] = useState<ResearchExecutionStatus>(
    enabled ? "loading" : "idle"
  );
  const [execution, setExecution] = useState<ResearchExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setStatus("idle");
      setExecution(null);
      setError(null);
      return;
    }

    const controller = new AbortController();
    setStatus("loading");
    setError(null);

    void (async () => {
      try {
        const result = await fetchResearchExecution({ signal: controller.signal });
        if (!controller.signal.aborted) {
          setExecution(result);
          setStatus("ready");
        }
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }
        setExecution(null);
        setStatus("error");
        setError(
          err instanceof ResearchExecutionApiError
            ? err.message
            : "Research execution unavailable. Invented metrics are not shown."
        );
      }
    })();

    return () => controller.abort();
  }, [enabled, reloadToken]);

  return { enabled, status, execution, error, reload };
}
