import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { WORKSPACE_NAV_GROUPS, isWorkspaceNavItemActive } from "@/lib/workspaceNav";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";

const APP_ROOT = join(process.cwd(), "app");

function readPage(relativePath: string): string {
  return readFileSync(join(APP_ROOT, relativePath), "utf8");
}

describe("Phase 2 route hygiene", () => {
  it("keeps exactly five primary navigation destinations", () => {
    const hrefs = WORKSPACE_NAV_GROUPS.flatMap((group) =>
      group.items.map((item) => item.href)
    );
    expect(hrefs).toEqual([
      "/",
      "/compare-models",
      "/strategy-lab",
      "/ai-insights",
      "/data-center",
    ]);
    expect(hrefs).toHaveLength(5);
  });

  it("marks Research Home active for research workspace routes", () => {
    expect(isWorkspaceNavItemActive("/research/ma-crossover-spy", "/")).toBe(true);
    expect(isWorkspaceNavItemActive("/compare-models", "/")).toBe(false);
  });

  it("permanently redirects /overview to Research Home", () => {
    const source = readPage("overview/page.tsx");
    expect(source).toMatch(/permanentRedirect\("\/"\)/);
  });

  it("permanently redirects /legacy to Research Home", () => {
    const source = readPage("legacy/page.tsx");
    expect(source).toMatch(/permanentRedirect\("\/"\)/);
  });

  it("permanently redirects /risk-gate-review into canonical robustness tab", () => {
    const source = readPage("risk-gate-review/page.tsx");
    expect(source).toMatch(/permanentRedirect/);
    expect(source).toContain("tab=robustness");
    expect(source).toContain("CANONICAL_RESEARCH_ID");
    expect(CANONICAL_RESEARCH_ID).toBe("ma-crossover-spy");
  });

  it("keeps secondary routes reachable from primary surfaces", () => {
    const insights = readFileSync(
      join(process.cwd(), "components/features/insights/AiInsightsPage.tsx"),
      "utf8"
    );
    const strategyLab = readFileSync(
      join(process.cwd(), "components/features/strategy-lab/StrategyLabPage.tsx"),
      "utf8"
    );
    expect(insights).toContain('href="/market-watch"');
    expect(strategyLab).toContain('href="/comparison"');
    expect(strategyLab).toContain('href="/experiments"');
  });
});
