"use client";

import { useCallback, useEffect, useState } from "react";
import { getDatabaseStatus } from "@/lib/api";

/**
 * Persistent run-archive capability (optional Supabase).
 * Separates save/list availability from deterministic backtest execution.
 */
export type RunArchiveAvailability =
  | "checking"
  | "available"
  | "not-configured"
  | "unavailable";

export type UseRunArchiveCapabilityResult = {
  availability: RunArchiveAvailability;
  canSave: boolean;
  isChecking: boolean;
  refresh: () => Promise<void>;
};

export function useRunArchiveCapability(
  options: { autoCheck?: boolean } = {}
): UseRunArchiveCapabilityResult {
  const autoCheck = options.autoCheck !== false;
  const [availability, setAvailability] =
    useState<RunArchiveAvailability>("checking");

  const refresh = useCallback(async () => {
    setAvailability("checking");
    try {
      const status = await getDatabaseStatus();
      if (!status.configured) {
        setAvailability("not-configured");
        return;
      }
      if (!status.connected) {
        setAvailability("unavailable");
        return;
      }
      setAvailability("available");
    } catch {
      setAvailability("unavailable");
    }
  }, []);

  useEffect(() => {
    if (!autoCheck) return;
    void refresh();
  }, [autoCheck, refresh]);

  return {
    availability,
    canSave: availability === "available",
    isChecking: availability === "checking",
    refresh,
  };
}
