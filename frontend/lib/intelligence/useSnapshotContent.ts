"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getPublishedSnapshotContent } from "@/lib/intelligence/api";
import {
  mapIntelligenceError,
  type IntelligenceUiError,
} from "@/lib/intelligence/errorMap";
import type {
  ResearchSummarySnapshot,
  SignalSnapshot,
  SnapshotContentDto,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";
import {
  isResearchSummarySnapshot,
  isSignalSnapshot,
} from "@/lib/intelligence/workspaceDisplay";

export type SnapshotContentStatus =
  | "idle"
  | "loading"
  | "ready"
  | "missing_reference"
  | "error";

export type UseSnapshotContentResult<T> = {
  status: SnapshotContentStatus;
  content: T | null;
  reference: SnapshotReferenceDto | null;
  error: IntelligenceUiError | null;
  retry: () => void;
};

type CacheEntry = {
  dto: SnapshotContentDto;
};

/**
 * Lazy snapshot-content loader with workspace-lifetime cache keyed by
 * `${runId}:${snapshotId}`. Hook must live in PublishedResearchWorkspace so
 * the Map survives Overview ↔ Evidence ↔ Signals navigation.
 * No module-global, React Query, SWR, or storage cache.
 */
export function useSnapshotContent<T>(
  runId: string,
  reference: SnapshotReferenceDto | null,
  enabled: boolean,
  guard: (content: unknown) => content is T,
  invalidMessage: string
): UseSnapshotContentResult<T> {
  const cacheRef = useRef<Map<string, CacheEntry>>(new Map());
  const [status, setStatus] = useState<SnapshotContentStatus>(
    reference ? (enabled ? "loading" : "idle") : "missing_reference"
  );
  const [content, setContent] = useState<T | null>(null);
  const [error, setError] = useState<IntelligenceUiError | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const retry = useCallback(() => {
    if (!reference) return;
    const key = `${runId}:${reference.snapshot_id}`;
    cacheRef.current.delete(key);
    setReloadToken((token) => token + 1);
  }, [reference, runId]);

  useEffect(() => {
    if (!enabled) {
      // Preserve cached ready/content for header enrichment and Validation
      // discrepancy while other views are active. Only clear when the
      // reference itself disappears.
      if (!reference) {
        setStatus("missing_reference");
        setContent(null);
        setError(null);
      }
      return;
    }
    if (!reference) {
      setStatus("missing_reference");
      setContent(null);
      setError(null);
      return;
    }

    const key = `${runId}:${reference.snapshot_id}`;
    const cached = cacheRef.current.get(key);
    if (cached) {
      if (guard(cached.dto.content)) {
        setContent(cached.dto.content);
        setStatus("ready");
        setError(null);
        return;
      }
      cacheRef.current.delete(key);
    }

    const controller = new AbortController();
    setStatus("loading");
    setError(null);

    void (async () => {
      try {
        const dto = await getPublishedSnapshotContent(
          runId,
          reference.snapshot_id
        );
        if (controller.signal.aborted) return;
        if (!guard(dto.content)) {
          setContent(null);
          setStatus("error");
          setError({
            category: "invalid_snapshot",
            reason: "snapshot_invalid",
            message: invalidMessage,
            runId,
            resourceId: reference.snapshot_id,
          });
          return;
        }
        cacheRef.current.set(key, { dto });
        setContent(dto.content);
        setStatus("ready");
      } catch (err) {
        if (controller.signal.aborted) return;
        setContent(null);
        setStatus("error");
        setError(mapIntelligenceError(err, "snapshot_content"));
      }
    })();

    return () => controller.abort();
  }, [enabled, guard, invalidMessage, reference, reloadToken, runId]);

  return {
    status,
    content,
    reference,
    error,
    retry,
  };
}

export function useSummarySnapshotContent(
  runId: string,
  reference: SnapshotReferenceDto | null,
  enabled: boolean
): UseSnapshotContentResult<ResearchSummarySnapshot> {
  return useSnapshotContent(
    runId,
    reference,
    enabled,
    isResearchSummarySnapshot,
    "Research summary snapshot content is invalid."
  );
}

export function useSignalSnapshotContent(
  runId: string,
  reference: SnapshotReferenceDto | null,
  enabled: boolean
): UseSnapshotContentResult<SignalSnapshot> {
  return useSnapshotContent(
    runId,
    reference,
    enabled,
    isSignalSnapshot,
    "Signal snapshot content is invalid."
  );
}
