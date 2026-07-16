"use client";

import { useCallback, useEffect, useState } from "react";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { getApiUserMessage } from "@/lib/apiRequest";
import { fetchResearchValidation } from "@/lib/researchValidationApi";
import type {
  ResearchValidationResult,
  ResearchValidationStatus,
} from "@/types/researchValidation";
import type { ResearchRunConfiguration } from "@/types/research";

export function useResearchValidation(
  researchId: string,
  enabled: boolean,
  configuration?: ResearchRunConfiguration
) {
  const requestEnabled =
    enabled && (researchId === CANONICAL_RESEARCH_ID || Boolean(configuration));
  const [status, setStatus] = useState<ResearchValidationStatus>("idle");
  const [validation, setValidation] =
    useState<ResearchValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  useEffect(() => {
    if (!requestEnabled) {
      setStatus("idle");
      setValidation(null);
      setError(null);
      return;
    }

    const controller = new AbortController();
    setStatus("loading");
    setValidation(null);
    setError(null);

    void (async () => {
      try {
        const result = await fetchResearchValidation({
          signal: controller.signal,
          researchId,
          configuration,
        });
        if (!controller.signal.aborted) {
          setValidation(result);
          setStatus("ready");
        }
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }
        setValidation(null);
        setStatus("error");
        setError(
          getApiUserMessage(
            err,
            "Research validation unavailable. Invented evidence is not shown."
          )
        );
      }
    })();

    return () => controller.abort();
  }, [configuration, reloadToken, requestEnabled, researchId]);

  return {
    enabled: requestEnabled,
    status,
    validation,
    error,
    reload,
  };
}
