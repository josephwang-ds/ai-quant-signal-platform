"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getLatestPublishedRun,
  listPublishedRuns,
} from "@/lib/intelligence/api";
import {
  distinctRunTypes,
  filterPublishedOnly,
  sortPublishedRuns,
} from "@/lib/intelligence/display";
import {
  classifyLatestPublishedRunError,
  mapIntelligenceError,
  type IntelligenceUiError,
} from "@/lib/intelligence/errorMap";
import type {
  ResearchRunDetailDto,
  ResearchRunSummaryDto,
  ResearchRunType,
} from "@/lib/intelligence/types";

export type PublishedRunsStatus =
  | "loading"
  | "ready"
  | "empty"
  | "error"
  | "inconsistent";

export type LatestSectionState =
  | { kind: "hidden" }
  | { kind: "ready"; run: ResearchRunDetailDto }
  | { kind: "unavailable"; error: IntelligenceUiError };

export type UsePublishedRunsResult = {
  status: PublishedRunsStatus;
  runs: ResearchRunSummaryDto[];
  filteredRuns: ResearchRunSummaryDto[];
  latest: LatestSectionState;
  listError: IntelligenceUiError | null;
  runTypeFilter: ResearchRunType | "all";
  availableRunTypes: ResearchRunType[];
  setRunTypeFilter: (value: ResearchRunType | "all") => void;
  reload: () => void;
};

/**
 * Owns Research Library list + latest fetches.
 * Failures are independent: latest_missing never becomes a page-level error.
 */
export function usePublishedRuns(): UsePublishedRunsResult {
  const [status, setStatus] = useState<PublishedRunsStatus>("loading");
  const [runs, setRuns] = useState<ResearchRunSummaryDto[]>([]);
  const [latest, setLatest] = useState<LatestSectionState>({ kind: "hidden" });
  const [listError, setListError] = useState<IntelligenceUiError | null>(null);
  const [runTypeFilter, setRunTypeFilter] = useState<ResearchRunType | "all">(
    "all"
  );
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    setListError(null);

    void (async () => {
      const [listResult, latestResult] = await Promise.allSettled([
        listPublishedRuns({ status: "PUBLISHED" }),
        getLatestPublishedRun(),
      ]);

      if (controller.signal.aborted) return;

      let nextRuns: ResearchRunSummaryDto[] = [];
      let listFailed: IntelligenceUiError | null = null;

      if (listResult.status === "fulfilled") {
        nextRuns = sortPublishedRuns(
          filterPublishedOnly(listResult.value.items ?? [])
        );
      } else {
        listFailed = mapIntelligenceError(listResult.reason, "run_detail");
      }

      let nextLatest: LatestSectionState = { kind: "hidden" };
      if (latestResult.status === "fulfilled") {
        const run = latestResult.value;
        if (run.status !== "PUBLISHED") {
          nextLatest = {
            kind: "unavailable",
            error: {
              category: "malformed_response",
              reason: "unknown",
              message:
                "Latest published run response was not a published run.",
            },
          };
        } else {
          nextLatest = { kind: "ready", run };
        }
      } else {
        const mapped = classifyLatestPublishedRunError(latestResult.reason);
        if (mapped.reason === "latest_missing") {
          nextLatest = { kind: "hidden" };
        } else {
          nextLatest = { kind: "unavailable", error: mapped };
        }
      }

      if (listFailed) {
        setRuns([]);
        setLatest(nextLatest);
        setListError(listFailed);
        setStatus("error");
        return;
      }

      // Prefer treating latest-with-empty-list as inconsistent transport state.
      if (nextRuns.length === 0 && nextLatest.kind === "ready") {
        setRuns([]);
        setLatest({ kind: "hidden" });
        setListError({
          category: "malformed_response",
          reason: "unknown",
          message:
            "Published run list is empty while a latest published run was returned. Retry to reload.",
        });
        setStatus("inconsistent");
        return;
      }

      setRuns(nextRuns);
      setLatest(nextLatest);
      setListError(null);
      setStatus(nextRuns.length === 0 ? "empty" : "ready");
    })();

    return () => controller.abort();
  }, [reloadToken]);

  const availableRunTypes = useMemo(() => distinctRunTypes(runs), [runs]);

  useEffect(() => {
    if (
      runTypeFilter !== "all" &&
      !availableRunTypes.includes(runTypeFilter)
    ) {
      setRunTypeFilter("all");
    }
  }, [availableRunTypes, runTypeFilter]);

  const filteredRuns = useMemo(() => {
    if (runTypeFilter === "all") return runs;
    return runs.filter((run) => run.run_type === runTypeFilter);
  }, [runs, runTypeFilter]);

  return {
    status,
    runs,
    filteredRuns,
    latest,
    listError,
    runTypeFilter,
    availableRunTypes,
    setRunTypeFilter,
    reload,
  };
}
