import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  LocalResearchRepository,
  RESEARCH_WORKSPACE_STORAGE_KEY,
} from "@/lib/localResearchRepository";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";

describe("LocalResearchRepository", () => {
  beforeEach(() => {
    const store = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
      clear: () => {
        store.clear();
      },
    });
    window.localStorage.removeItem(RESEARCH_WORKSPACE_STORAGE_KEY);
  });

  it("includes demo research by default", async () => {
    const repo = new LocalResearchRepository();
    const list = await repo.list();
    expect(list.some((item) => item.id === CANONICAL_RESEARCH_ID)).toBe(true);
  });

  it("creates research-first user research without run configuration", async () => {
    const repo = new LocalResearchRepository();
    const created = await repo.create({
      name: "Trend Following Study",
      researchQuestion:
        "Can moving average strategies consistently outperform Buy & Hold after transaction costs?",
      hypothesis:
        "Medium-term trend rules may reduce drawdowns, but any edge may weaken after costs and in sideways markets.",
      tags: ["trend-following", "draft"],
      owner: "Analyst",
    });

    expect(created.id).toMatch(/^research-/);
    expect(created.status).toBe("Draft");
    expect(created.experimentCount).toBe(0);
    expect(created.hypothesis).toContain("Medium-term trend rules");
    expect(created.evidenceSummary).toBe("No calculated evidence yet.");
    expect(created.runConfiguration).toBeUndefined();
    expect(created.configuration.strategyName).toBe("Not configured");

    const list = await repo.list();
    expect(list.some((item) => item.id === created.id)).toBe(true);
    expect(list.find((item) => item.id === created.id)?.name).toBe(
      "Trend Following Study"
    );
    expect(list.find((item) => item.id === created.id)?.evidenceSummary).toBe(
      "No calculated evidence yet."
    );
  });

  it("persists executable configuration for newly configured research", async () => {
    const repo = new LocalResearchRepository();
    const created = await repo.create({
      name: "Configured SPY study",
      researchQuestion: "Does a moving-average rule improve drawdown?",
      hypothesis: "A medium-term trend rule may reduce drawdown.",
      tags: ["trend"],
      runConfiguration: {
        symbol: "SPY",
        benchmark: "SPY",
        startDate: "2018-01-01",
        endDate: null,
        shortWindow: 20,
        longWindow: 60,
        transactionCost: 0.001,
        riskFreeRate: 0,
      },
    });

    expect(created.runConfiguration).toMatchObject({
      symbol: "SPY",
      shortWindow: 20,
      longWindow: 60,
    });
    expect(created.configuration.strategyName).toBe("Moving Average Crossover");
    expect(created.configuration.parameterLines).toContain("MA 20/60");
    expect((await repo.getById(created.id))?.runConfiguration).toEqual(
      created.runConfiguration
    );
  });

  it("rejects create without hypothesis", async () => {
    const repo = new LocalResearchRepository();
    await expect(
      repo.create({
        name: "Incomplete",
        researchQuestion: "Will this persist?",
        hypothesis: "   ",
        tags: [],
      })
    ).rejects.toThrow("Hypothesis is required.");
  });

  it("permanently removes user research from local storage", async () => {
    const repo = new LocalResearchRepository();
    const created = await repo.create({
      name: "Temporary local research",
      researchQuestion: "Should this research remain?",
      hypothesis: "This temporary research should be removable.",
      tags: [],
    });

    await repo.deletePermanently(created.id);

    expect(await repo.getById(created.id)).toBeNull();
    expect((await repo.list()).some((item) => item.id === created.id)).toBe(false);
    const persisted = window.localStorage.getItem(RESEARCH_WORKSPACE_STORAGE_KEY);
    expect(persisted).not.toContain(created.id);
    expect(persisted).not.toContain("Temporary local research");
  });

  it("does not permanently delete the built-in demo research", async () => {
    const repo = new LocalResearchRepository();

    await expect(repo.deletePermanently(CANONICAL_RESEARCH_ID)).rejects.toThrow(
      "cannot be permanently deleted"
    );
    expect((await repo.list()).some((item) => item.id === CANONICAL_RESEARCH_ID)).toBe(
      true
    );
  });

  it("hides demo research on archive and restores via includeDemoResearch", async () => {
    const repo = new LocalResearchRepository();
    await repo.archive(CANONICAL_RESEARCH_ID);
    expect((await repo.list()).some((item) => item.id === CANONICAL_RESEARCH_ID)).toBe(
      false
    );
    await repo.includeDemoResearch();
    expect((await repo.list()).some((item) => item.id === CANONICAL_RESEARCH_ID)).toBe(
      true
    );
  });
});
