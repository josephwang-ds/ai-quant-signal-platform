"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getPublishedRunDetail,
  listPublishedRunArtifacts,
  listPublishedRunSnapshots,
} from "@/lib/intelligence/api";
import {
  mapIntelligenceError,
  type IntelligenceUiError,
} from "@/lib/intelligence/errorMap";
import type {
  ArtifactReferenceDto,
  ResearchRunDetailDto,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";

export type PublishedRunGateStatus =
  | "loading"
  | "ready"
  | "not_found"
  | "not_published"
  | "unavailable"
  | "error";

export type ReferenceListState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; items: T[] }
  | { status: "error"; error: IntelligenceUiError };

export type UsePublishedRunResult = {
  gateStatus: PublishedRunGateStatus;
  gateError: IntelligenceUiError | null;
  run: ResearchRunDetailDto | null;
  artifacts: ReferenceListState<ArtifactReferenceDto>;
  snapshots: ReferenceListState<SnapshotReferenceDto>;
  retryGate: () => void;
  retryArtifacts: () => void;
  retrySnapshots: () => void;
};

function isUnavailableGateError(error: IntelligenceUiError): boolean {
  return (
    error.category === "malformed_response" ||
    error.backendCode === "INVALID_RUN_ID"
  );
}

/**
 * Hard-gates on run detail, then loads artifact/snapshot references.
 * Workspace-scoped only — no module-global cache, no snapshot content fetch.
 */
export function usePublishedRun(runId: string): UsePublishedRunResult {
  const [gateStatus, setGateStatus] = useState<PublishedRunGateStatus>("loading");
  const [gateError, setGateError] = useState<IntelligenceUiError | null>(null);
  const [run, setRun] = useState<ResearchRunDetailDto | null>(null);
  const [artifacts, setArtifacts] = useState<ReferenceListState<ArtifactReferenceDto>>({
    status: "idle",
  });
  const [snapshots, setSnapshots] = useState<ReferenceListState<SnapshotReferenceDto>>({
    status: "idle",
  });
  const [gateToken, setGateToken] = useState(0);
  const [artifactToken, setArtifactToken] = useState(0);
  const [snapshotToken, setSnapshotToken] = useState(0);

  const retryGate = useCallback(() => {
    setGateToken((token) => token + 1);
  }, []);

  const retryArtifacts = useCallback(() => {
    setArtifactToken((token) => token + 1);
  }, []);

  const retrySnapshots = useCallback(() => {
    setSnapshotToken((token) => token + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setGateStatus("loading");
    setGateError(null);
    setRun(null);
    setArtifacts({ status: "idle" });
    setSnapshots({ status: "idle" });

    void (async () => {
      try {
        const detail = await getPublishedRunDetail(runId);
        if (controller.signal.aborted) return;
        if (detail.status !== "PUBLISHED") {
          setGateStatus("not_published");
          setGateError({
            category: "not_published",
            reason: "run_not_published",
            message: "This run is not available as published research.",
            runId,
          });
          return;
        }
        setRun(detail);
        setGateStatus("ready");
      } catch (error) {
        if (controller.signal.aborted) return;
        const mapped = mapIntelligenceError(error, "run_detail");
        setGateError(mapped);
        if (mapped.reason === "run_not_found") {
          setGateStatus("not_found");
        } else if (mapped.reason === "run_not_published") {
          setGateStatus("not_published");
        } else if (isUnavailableGateError(mapped)) {
          setGateStatus("unavailable");
        } else {
          setGateStatus("error");
        }
      }
    })();

    return () => controller.abort();
  }, [gateToken, runId]);

  useEffect(() => {
    if (gateStatus !== "ready") return;
    const controller = new AbortController();
    setArtifacts({ status: "loading" });

    void (async () => {
      try {
        const result = await listPublishedRunArtifacts(runId);
        if (controller.signal.aborted) return;
        setArtifacts({ status: "ready", items: result.items ?? [] });
      } catch (error) {
        if (controller.signal.aborted) return;
        setArtifacts({
          status: "error",
          error: mapIntelligenceError(error, "run_artifacts"),
        });
      }
    })();

    return () => controller.abort();
  }, [artifactToken, gateStatus, runId]);

  useEffect(() => {
    if (gateStatus !== "ready") return;
    const controller = new AbortController();
    setSnapshots({ status: "loading" });

    void (async () => {
      try {
        const result = await listPublishedRunSnapshots(runId);
        if (controller.signal.aborted) return;
        setSnapshots({ status: "ready", items: result.items ?? [] });
      } catch (error) {
        if (controller.signal.aborted) return;
        setSnapshots({
          status: "error",
          error: mapIntelligenceError(error, "run_snapshots"),
        });
      }
    })();

    return () => controller.abort();
  }, [gateStatus, runId, snapshotToken]);

  return useMemo(
    () => ({
      gateStatus,
      gateError,
      run,
      artifacts,
      snapshots,
      retryGate,
      retryArtifacts,
      retrySnapshots,
    }),
    [
      artifacts,
      gateError,
      gateStatus,
      retryArtifacts,
      retryGate,
      retrySnapshots,
      run,
      snapshots,
    ]
  );
}
