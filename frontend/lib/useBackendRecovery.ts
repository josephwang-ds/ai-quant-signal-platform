"use client";

import { useEffect } from "react";
import {
  subscribeBackendReadiness,
  type BackendReadinessState,
} from "@/lib/apiRequest";

type RecoverableRequestStatus = "idle" | "loading" | "ready" | "error" | string;

/**
 * Re-run a failed evidence request once the shared backend wake-up succeeds.
 *
 * The initial ready event is ignored while a request is still loading, so this
 * does not duplicate normal requests. It only repairs panels that already
 * entered an error state during a cold start.
 */
export function useBackendRecovery(
  status: RecoverableRequestStatus,
  recover: () => void
): void {
  useEffect(() => {
    if (status !== "error") return;

    const handleReadiness = (readiness: BackendReadinessState) => {
      if (readiness === "ready") {
        recover();
      }
    };

    return subscribeBackendReadiness(handleReadiness);
  }, [recover, status]);
}
