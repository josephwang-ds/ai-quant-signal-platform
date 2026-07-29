import { describe, expect, it } from "vitest";
import {
  PRODUCT_BLURB,
  PRODUCT_NAME,
  PRODUCT_PHILOSOPHY,
  PRODUCT_TAGLINE,
} from "@/lib/productIdentity";
import { PLATFORM } from "@/lib/platformArchitecture";

describe("canonical product slogan", () => {
  it("locks the English name, tagline, and philosophy for README / site / resume reuse", () => {
    expect(PRODUCT_NAME).toBe("AI Investment Intelligence Platform");
    expect(PRODUCT_TAGLINE).toBe(
      "Built on an Evidence-driven Quant Research Engine."
    );
    expect(PRODUCT_PHILOSOPHY).toBe(
      "Every AI insight is backed by structured research evidence. Explainable. Traceable. Reviewable."
    );
    expect(PRODUCT_BLURB).toContain(PRODUCT_TAGLINE);
    expect(PRODUCT_BLURB).toContain(PRODUCT_PHILOSOPHY);
  });

  it("keeps the platform homepage copy in sync with productIdentity", () => {
    expect(PLATFORM.nameEn).toBe(PRODUCT_NAME);
    expect(PLATFORM.taglineEn).toBe(PRODUCT_TAGLINE);
    expect(PLATFORM.principleEn).toBe(PRODUCT_PHILOSOPHY);
  });
});
