import { describe, expect, it } from "vitest";
import { WORKSPACE_NAV_GROUPS, isWorkspaceNavItemActive } from "@/lib/workspaceNav";
import { ENGINE_STAGES, getContinueTarget } from "@/lib/platformArchitecture";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";

const APP_ROOT = join(process.cwd(), "app");

function readPage(relativePath: string): string {
  return readFileSync(join(APP_ROOT, relativePath), "utf8");
}

describe("IA V2 route hygiene", () => {
  it("keeps Library first and removes unfinished intelligence placeholders from primary nav", () => {
    expect(WORKSPACE_NAV_GROUPS.map((group) => group.id)).toEqual([
      "primary",
      "engine",
      "documentation",
    ]);
    const hrefs = WORKSPACE_NAV_GROUPS.flatMap((group) =>
      group.items.map((item) => item.href)
    );
    expect(hrefs).toContain("/");
    expect(hrefs).toContain("/market-watch");
    expect(hrefs).toContain("/platform");
    expect(hrefs).toContain("/engine");
    expect(hrefs).toContain("/engine/features");
    expect(hrefs[0]).toBe("/");
    expect(hrefs).not.toContain("/intelligence/market");
    expect(hrefs).not.toContain("/intelligence/research");
    expect(hrefs).not.toContain("/intelligence/signal");
    expect(hrefs).not.toContain("/experiments");
    expect(hrefs).not.toContain("/compare-models");
    expect(hrefs.every((href) => !href.includes("stage="))).toBe(true);
  });

  it("marks Research Library active on published run routes, not engine routes", () => {
    expect(isWorkspaceNavItemActive("/", "/")).toBe(true);
    expect(isWorkspaceNavItemActive("/engine", "/")).toBe(false);
    expect(isWorkspaceNavItemActive("/research/run_20260728T041530Z_a1b2c3d4", "/")).toBe(
      true
    );
    expect(isWorkspaceNavItemActive("/engine/research/ma-crossover-spy", "/")).toBe(false);
  });

  it("marks engine stage routes active precisely", () => {
    expect(isWorkspaceNavItemActive("/engine/portfolio", "/engine/portfolio")).toBe(
      true
    );
    expect(isWorkspaceNavItemActive("/engine/portfolio", "/engine")).toBe(false);
    expect(isWorkspaceNavItemActive("/engine/data", "/engine/portfolio")).toBe(
      false
    );
  });

  it("permanently redirects /overview to Platform Overview", () => {
    const source = readPage("overview/page.tsx");
    expect(source).toMatch(/permanentRedirect\("\/platform"\)/);
  });

  it("permanently redirects /legacy to Platform Overview", () => {
    const source = readPage("legacy/page.tsx");
    expect(source).toMatch(/permanentRedirect\("\/platform"\)/);
  });

  it("permanently redirects /risk-gate-review into the engine catalog robustness tab", () => {
    const source = readPage("risk-gate-review/page.tsx");
    expect(source).toMatch(/permanentRedirect/);
    expect(source).toContain("tab=robustness");
    expect(source).toContain("/engine/research/");
    expect(source).toContain("CANONICAL_RESEARCH_ID");
    expect(CANONICAL_RESEARCH_ID).toBe("ma-crossover-spy");
  });

  it("keeps new catalog workspace links on /engine/research, not legacy /research", () => {
    const engineHome = readFileSync(
      join(process.cwd(), "components/features/platform/ResearchEngineHomePage.tsx"),
      "utf8"
    );
    const card = readFileSync(
      join(process.cwd(), "components/features/research/ResearchCard.tsx"),
      "utf8"
    );
    expect(engineHome).toContain("/engine/research/");
    expect(engineHome).not.toMatch(/href=\{`\/research\/\$\{/);
    expect(card).toContain("/engine/research/");
    expect(card).not.toMatch(/`\/research\/\$\{/);
  });
  it("redirects /experiments into the Backtesting engine stage", () => {
    const source = readPage("experiments/page.tsx");
    expect(source).toMatch(/permanentRedirect/);
    expect(source).toContain("/engine/backtest");
  });

  it("moves the platform home content to /platform and keeps / as the library route", () => {
    const platform = readPage("platform/page.tsx");
    const home = readPage("page.tsx");
    expect(platform).toContain("PlatformHomePage");
    expect(home).toContain("ResearchLibraryPage");
    expect(home).not.toContain("PlatformHomePage");
    expect(home).not.toContain("ResearchLibraryPlaceholderPage");
  });

  it("keeps secondary tools reachable from primary surfaces", () => {
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
    expect(strategyLab).toContain('href="/engine/backtest"');
  });

  it("defines eight engine stages with portfolio as continue target", () => {
    expect(ENGINE_STAGES).toHaveLength(8);
    expect(getContinueTarget().id).toBe("portfolio");
  });
});
