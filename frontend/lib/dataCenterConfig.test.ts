import { describe, expect, it } from "vitest";
import {
  ASSET_CLASS_ROWS,
  PRICE_ONLY_ROWS,
  RESEARCH_READY_ROWS,
  SYMBOL_FORMAT_ROWS,
  coverageStatusBadgeVariant,
  coverageStatusLabelKey,
} from "@/lib/dataCenterConfig";
import {
  ENGINE_STAGES,
  US_LIQUID_31_SYMBOLS,
  getContinueTarget,
  stageStatusLabel,
} from "@/lib/platformArchitecture";

describe("dataCenterConfig", () => {
  it("publishes research-ready rows without partially-available prominence", () => {
    expect(RESEARCH_READY_ROWS.map((row) => row.id)).toEqual([
      "us-stocks",
      "etfs",
      "hk-stocks",
      "cn-akshare",
    ]);
    expect(
      RESEARCH_READY_ROWS.find((row) => row.id === "us-stocks")?.readiness
    ).toBe("full_cross_sectional");
    expect(PRICE_ONLY_ROWS).toHaveLength(1);
    expect(PRICE_ONLY_ROWS[0]?.id).toBe("indexes-fx-crypto");
  });

  it("keeps legacy asset-class ids aligned with research-ready markets", () => {
    expect(ASSET_CLASS_ROWS.map((row) => row.id)).toEqual([
      "us-stocks",
      "etfs",
      "hk-stocks",
      "cn-akshare",
    ]);
    expect(ASSET_CLASS_ROWS.every((row) => row.status === "active")).toBe(true);
    expect(SYMBOL_FORMAT_ROWS.map((row) => row.id)).toEqual([
      "us",
      "etf",
      "hk",
      "sh",
      "sz",
    ]);
  });

  it("maps the single public coverage state consistently", () => {
    expect(coverageStatusLabelKey("active")).toBe("statusActive");
    expect(coverageStatusBadgeVariant("active")).toBe("success");
  });
});

describe("guided engine content", () => {
  it("defines eight stages with portfolio as the continue target", () => {
    expect(ENGINE_STAGES).toHaveLength(8);
    expect(ENGINE_STAGES.map((stage) => stage.status)).toEqual([
      "completed",
      "completed",
      "completed",
      "completed",
      "completed",
      "current",
      "locked",
      "locked",
    ]);
    expect(getContinueTarget().id).toBe("portfolio");
    expect(stageStatusLabel("locked", "en")).toBe("Locked");
    expect(stageStatusLabel("current", "zh")).toBe("当前");
  });

  it("exposes the full static US Liquid 31 membership", () => {
    expect(US_LIQUID_31_SYMBOLS).toHaveLength(31);
    expect(US_LIQUID_31_SYMBOLS.includes("BRK-B")).toBe(true);
  });
});
