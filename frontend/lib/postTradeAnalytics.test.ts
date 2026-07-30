import { describe, expect, it } from "vitest";
import {
  DEMO_ANOMALY_REQUEST,
  DEMO_ATTRIBUTION_REQUEST,
} from "@/lib/postTradeAnalytics";

describe("post-trade demo contracts", () => {
  it("labels both fixtures as synthetic and keeps trade identities unique", () => {
    expect(DEMO_ATTRIBUTION_REQUEST.input_data_kind).toBe("synthetic_demo");
    expect(DEMO_ANOMALY_REQUEST.input_data_kind).toBe("synthetic_demo");
    const ids = DEMO_ATTRIBUTION_REQUEST.observations.map(
      (item) => item.trade_id
    );
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("uses a past-only-compatible anomaly configuration", () => {
    expect(DEMO_ANOMALY_REQUEST.minimum_history).toBeLessThanOrEqual(
      DEMO_ANOMALY_REQUEST.baseline_window
    );
    expect(DEMO_ANOMALY_REQUEST.direction).toBe("high");
    expect(
      DEMO_ANOMALY_REQUEST.observations.some((item) => item.value > 3)
    ).toBe(true);
  });
});
