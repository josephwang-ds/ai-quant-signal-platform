import { describe, expect, it } from "vitest";
import {
  comparePublishedRuns,
  derivePublishedRunLabel,
  distinctRunTypes,
  filterPublishedOnly,
  formatNullableText,
  sortPublishedRuns,
  summarizeUniverse,
} from "@/lib/intelligence/display";
import type { ResearchRunSummaryDto } from "@/lib/intelligence/types";

function run(
  partial: Partial<ResearchRunSummaryDto> & Pick<ResearchRunSummaryDto, "run_id">
): ResearchRunSummaryDto {
  return {
    run_type: "TREND",
    status: "PUBLISHED",
    created_at: "2026-07-28T04:15:30Z",
    updated_at: "2026-07-28T04:15:30Z",
    published_at: "2026-07-28T04:15:30Z",
    universe: null,
    dataset_version: null,
    feature_version: null,
    model_version: null,
    git_commit: null,
    artifact_count: 0,
    snapshot_count: 0,
    ...partial,
  };
}

describe("intelligence display helpers", () => {
  it("derives presentation labels without inventing metrics", () => {
    expect(
      derivePublishedRunLabel(
        run({ run_id: "run_a", run_type: "FACTOR", universe: "US Large Cap" })
      )
    ).toBe("Factor Research · US Large Cap");
    expect(derivePublishedRunLabel(run({ run_id: "run_b", run_type: "MODEL" }))).toBe(
      "Model Research"
    );
  });

  it("summarizes long universe lists", () => {
    expect(summarizeUniverse("AAPL, MSFT, NVDA, AMZN, META")).toBe(
      "AAPL, MSFT, NVDA +2"
    );
    expect(summarizeUniverse(null)).toBeNull();
  });

  it("renders nullable text as em dash", () => {
    expect(formatNullableText(null)).toBe("—");
    expect(formatNullableText("")).toBe("—");
    expect(formatNullableText("v3")).toBe("v3");
  });

  it("sorts by published_at DESC then run_id ASC", () => {
    const sorted = sortPublishedRuns([
      run({ run_id: "run_b", published_at: "2026-07-28T10:00:00Z" }),
      run({ run_id: "run_a", published_at: "2026-07-28T10:00:00Z" }),
      run({ run_id: "run_c", published_at: "2026-07-29T10:00:00Z" }),
    ]);
    expect(sorted.map((item) => item.run_id)).toEqual([
      "run_c",
      "run_a",
      "run_b",
    ]);
    expect(comparePublishedRuns(sorted[0], sorted[1])).toBeLessThan(0);
  });

  it("drops non-published statuses defensively", () => {
    expect(
      filterPublishedOnly([
        run({ run_id: "run_ok" }),
        run({ run_id: "run_bad", status: "ARCHIVED" }),
      ]).map((item) => item.run_id)
    ).toEqual(["run_ok"]);
  });

  it("orders distinct run types stably", () => {
    expect(
      distinctRunTypes([
        run({ run_id: "1", run_type: "MODEL" }),
        run({ run_id: "2", run_type: "TREND" }),
        run({ run_id: "3", run_type: "MODEL" }),
      ])
    ).toEqual(["TREND", "MODEL"]);
  });
});
