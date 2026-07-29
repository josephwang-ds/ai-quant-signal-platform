import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("Phase 4.6 Research Library route", () => {
  it("serves the live Library client from / without the 4.6A placeholder", () => {
    const home = readFileSync(join(process.cwd(), "app/page.tsx"), "utf8");
    expect(home).toContain("ResearchLibraryPage");
    expect(home).not.toContain("ResearchLibraryPlaceholderPage");
    expect(home).not.toMatch(/mock published runs/i);
  });
});
