import { describe, expect, it } from "vitest";
import {
  countSignalsByDirection,
  formatByteSize,
  formatNullableNumber,
  formatSignalDirection,
  formatValidationStatus,
  hasSummaryValidationDiscrepancy,
  isResearchSummarySnapshot,
  isSignalSnapshot,
  mapRunValidationOk,
  resolveWorkspaceView,
  selectSnapshotReference,
  sortSignalRecords,
  truncateChecksum,
  workspaceViewHref,
} from "@/lib/intelligence/workspaceDisplay";
import type {
  ResearchSummarySnapshot,
  SignalRecord,
  SignalSnapshot,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";

function snap(
  partial: Partial<SnapshotReferenceDto> &
    Pick<SnapshotReferenceDto, "snapshot_id" | "snapshot_type" | "created_at">
): SnapshotReferenceDto {
  return {
    name: partial.name ?? "misleading-name-as-signal",
    schema_version: "v1",
    media_type: "application/json",
    checksum_algorithm: "sha256",
    checksum: "abcdef0123456789fedcba9876543210",
    size_bytes: 128,
    as_of: null,
    source_artifact_ids: [],
    ...partial,
  };
}

function validSummary(
  overrides: Partial<ResearchSummarySnapshot> = {}
): ResearchSummarySnapshot {
  return {
    schema_version: "research-summary-snapshot/v1",
    generated_at: "2026-07-28T04:20:00Z",
    as_of: null,
    research_title: "Title",
    research_objective: null,
    run_type: "FACTOR",
    universe: null,
    analysis_window: null,
    validation_status: "passed",
    key_findings: [{ code: null, statement: "Stable", category: null }],
    limitations: [{ code: null, statement: "Short window" }],
    artifact_summary: [],
    provenance: {
      source_artifact_ids: [],
      builder: "builder",
      notes: null,
    },
    ...overrides,
  };
}

function validSignal(overrides: Partial<SignalSnapshot> = {}): SignalSnapshot {
  return {
    schema_version: "signal-snapshot/v1",
    generated_at: "2026-07-28T04:20:00Z",
    as_of: null,
    universe: null,
    signals: [
      {
        symbol: "AAPL",
        signal_name: "momentum",
        direction: "positive",
        score: null,
        confidence: null,
        horizon: null,
        evidence_artifact_ids: [],
        metadata: {},
      },
    ],
    provenance: {
      source_artifact_ids: [],
      builder: "builder",
      notes: null,
    },
    ...overrides,
  };
}

describe("workspaceDisplay selection and formatting (Phase 4.6C2)", () => {
  it("resolves views and builds hrefs", () => {
    expect(resolveWorkspaceView(null)).toBe("overview");
    expect(resolveWorkspaceView("signals")).toBe("signals");
    expect(resolveWorkspaceView("nope")).toBe("overview");
    expect(workspaceViewHref("run_abc", "overview")).toBe("/research/run_abc");
    expect(workspaceViewHref("run_abc", "evidence")).toBe(
      "/research/run_abc?view=evidence"
    );
  });

  it("selects by exact type, newest created_at, then snapshot_id ascending", () => {
    const selected = selectSnapshotReference(
      [
        snap({
          snapshot_id: "snap_b",
          snapshot_type: "research_summary",
          created_at: "2026-07-28T10:00:00Z",
          name: "signal",
        }),
        snap({
          snapshot_id: "snap_a",
          snapshot_type: "research_summary",
          created_at: "2026-07-28T10:00:00Z",
          name: "also-signal",
        }),
        snap({
          snapshot_id: "snap_old",
          snapshot_type: "research_summary",
          created_at: "2026-07-27T10:00:00Z",
        }),
        snap({
          snapshot_id: "snap_signal",
          snapshot_type: "signal",
          created_at: "2026-07-29T10:00:00Z",
          name: "research_summary",
        }),
      ],
      "research_summary"
    );
    expect(selected?.snapshot_id).toBe("snap_a");

    const signal = selectSnapshotReference(
      [
        snap({
          snapshot_id: "snap_signal",
          snapshot_type: "signal",
          created_at: "2026-07-28T10:00:00Z",
        }),
        snap({
          snapshot_id: "named-summary",
          snapshot_type: "research_summary",
          created_at: "2026-07-29T10:00:00Z",
          name: "signal",
        }),
      ],
      "signal"
    );
    expect(signal?.snapshot_id).toBe("snap_signal");
    expect(selectSnapshotReference([], "signal")).toBeNull();
  });

  it("sorts signals and formats neutral directions without Buy/Sell", () => {
    const signals: SignalRecord[] = [
      {
        symbol: "MSFT",
        signal_name: "trend",
        direction: "positive",
        score: null,
        confidence: null,
        horizon: null,
        evidence_artifact_ids: [],
        metadata: {},
      },
      {
        symbol: "AAPL",
        signal_name: "z",
        direction: "strong_negative",
        score: 1,
        confidence: 0.2,
        horizon: "5d",
        evidence_artifact_ids: [],
        metadata: {},
      },
      {
        symbol: "AAPL",
        signal_name: "a",
        direction: "neutral",
        score: null,
        confidence: null,
        horizon: null,
        evidence_artifact_ids: [],
        metadata: {},
      },
    ];
    expect(sortSignalRecords(signals).map((s) => `${s.symbol}:${s.signal_name}`)).toEqual([
      "AAPL:a",
      "AAPL:z",
      "MSFT:trend",
    ]);
    expect(formatSignalDirection("strong_positive", "en")).toBe("Strong positive");
    expect(formatSignalDirection("strong_negative", "en")).not.toMatch(/buy|sell/i);
    expect(countSignalsByDirection(signals).neutral).toBe(1);
    expect(formatNullableNumber(null)).toBe("—");
    expect(formatNullableNumber(Number.NaN)).toBe("—");
    expect(formatNullableNumber(Number.POSITIVE_INFINITY)).toBe("—");
    expect(formatNullableNumber(1.25)).toBe("1.25");
  });

  it("formats checksums/bytes and detects validation discrepancy only for passed/failed", () => {
    expect(truncateChecksum("abcdefghijklmnop")).toBe("abcdef…klmnop");
    expect(formatByteSize(2048)).toBe("2.0 KB");
    expect(mapRunValidationOk(true)).toBe("passed");
    expect(formatValidationStatus("passed", "en")).toBe("Passed");
    expect(formatValidationStatus("failed", "en")).toBe("Failed");
    expect(hasSummaryValidationDiscrepancy(true, "failed")).toBe(true);
    expect(hasSummaryValidationDiscrepancy(true, "passed")).toBe(false);
    expect(hasSummaryValidationDiscrepancy(false, "unknown")).toBe(false);
    expect(hasSummaryValidationDiscrepancy(false, "not_started")).toBe(false);
    expect(hasSummaryValidationDiscrepancy(true, "in_progress")).toBe(false);
  });
});

describe("snapshot content guards (Phase 4.6C2)", () => {
  it("accepts valid summary and signal contracts", () => {
    expect(isResearchSummarySnapshot(validSummary())).toBe(true);
    expect(isSignalSnapshot(validSignal())).toBe(true);
  });

  it("rejects wrong schemas and invalid findings/directions/numbers", () => {
    expect(
      isResearchSummarySnapshot(
        validSummary({ schema_version: "signal-snapshot/v1" as never })
      )
    ).toBe(false);
    expect(
      isSignalSnapshot(
        validSignal({ schema_version: "research-summary-snapshot/v1" as never })
      )
    ).toBe(false);
    expect(
      isResearchSummarySnapshot(
        validSummary({
          key_findings: [{ code: null, statement: 12 as never, category: null }],
        })
      )
    ).toBe(false);
    expect(
      isSignalSnapshot(
        validSignal({
          signals: [
            {
              symbol: "AAPL",
              signal_name: "m",
              direction: "buy" as never,
              score: null,
              confidence: null,
              horizon: null,
              evidence_artifact_ids: [],
              metadata: {},
            },
          ],
        })
      )
    ).toBe(false);
    expect(
      isSignalSnapshot(
        validSignal({
          signals: [
            {
              symbol: "AAPL",
              signal_name: "m",
              direction: "positive",
              score: "0.2" as never,
              confidence: null,
              horizon: null,
              evidence_artifact_ids: [],
              metadata: {},
            },
          ],
        })
      )
    ).toBe(false);
    expect(isResearchSummarySnapshot({ not: "a summary" })).toBe(false);
    expect(isSignalSnapshot({ raw: true })).toBe(false);
  });
});
