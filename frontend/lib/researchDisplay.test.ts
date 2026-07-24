import { describe, expect, it } from "vitest";
import {
  timelineEventKindLabel,
  timelineEventSummaryLabel,
  timelineEventTitleLabel,
} from "@/lib/researchDisplay";

describe("research timeline localization", () => {
  it("localizes canonical timeline content in Chinese", () => {
    expect(
      timelineEventTitleLabel("Research Definition Created", "zh")
    ).toBe("已创建研究定义");
    expect(
      timelineEventSummaryLabel(
        "Canonical Trend Following Study defined for the public Research Hub.",
        "zh"
      )
    ).toBe("已为公开研究工作区定义标准趋势跟踪案例。");
    expect(timelineEventKindLabel("stage_change", "zh")).toBe("阶段变更");
  });

  it("preserves user-authored or unknown content", () => {
    expect(timelineEventTitleLabel("Custom event", "zh")).toBe("Custom event");
    expect(timelineEventTitleLabel("Research Definition Created", "en")).toBe(
      "Research Definition Created"
    );
  });
});
