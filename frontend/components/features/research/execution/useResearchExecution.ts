"use client";

import { useCallback, useEffect, useState } from "react";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { getApiDisplayMessage } from "@/lib/apiRequest";
import { fetchResearchExecution } from "@/lib/researchExecutionApi";
import type {
  ResearchExecutionResult,
  ResearchExecutionStatus,
} from "@/types/researchExecution";
import type { ResearchRunConfiguration } from "@/types/research";

export function useResearchExecution(
  researchId: string,
  configuration?: ResearchRunConfiguration
) {
  const enabled = researchId === CANONICAL_RESEARCH_ID || Boolean(configuration);
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
        const result = await fetchResearchExecution({
          signal: controller.signal,
          researchId,
          configuration,
        });
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
          getApiDisplayMessage(
            err,
            "Research execution unavailable. Invented metrics are not shown."
          )
        );
      }
    })();

    return () => controller.abort();
  }, [configuration, enabled, reloadToken, researchId]);

  return { enabled, status, execution, error, reload };
}
