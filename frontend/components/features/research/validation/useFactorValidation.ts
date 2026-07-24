"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { CANONICAL_FACTOR_RESEARCH_ID } from "@/lib/canonicalCrossSectionalFactor";
import { getLocalizedApiDisplayMessage } from "@/lib/apiRequest";
import { fetchFactorValidation } from "@/lib/factorValidationApi";
import { useBackendRecovery } from "@/lib/useBackendRecovery";
import type { Language } from "@/lib/i18n";
import type {
  FactorValidationResult,
  FactorValidationStatus,
} from "@/types/factorValidation";
import type { FactorRunConfiguration } from "@/types/research";

export function useFactorValidation(
  researchId: string,
  enabled: boolean,
  configuration: FactorRunConfiguration | undefined,
  language: Language = "en"
) {
  const requestEnabled =
    enabled &&
    (researchId === CANONICAL_FACTOR_RESEARCH_ID || Boolean(configuration));
  const [status, setStatus] = useState<FactorValidationStatus>("idle");
  const [validation, setValidation] = useState<FactorValidationResult | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);
  const languageRef = useRef(language);
  languageRef.current = language;

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);
  useBackendRecovery(status, reload);

  useEffect(() => {
    if (!requestEnabled || !configuration) {
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
        const result = await fetchFactorValidation({
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
          getLocalizedApiDisplayMessage(
            err,
            languageRef.current,
            "Factor validation unavailable. Invented evidence is not shown."
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
