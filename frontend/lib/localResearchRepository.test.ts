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

  it("creates user research in localStorage", async () => {
    const repo = new LocalResearchRepository();
    const created = await repo.create({
      name: "Configurable MA Study",
      researchQuestion: "Does MA10/50 improve drawdown on QQQ?",
      symbol: "QQQ",
      benchmark: "QQQ",
      startDate: "2020-01-01",
      endDate: "2025-12-31",
      shortWindow: 10,
      longWindow: 50,
      transactionCost: 0.002,
      tags: ["draft", "qqq"],
      owner: "Analyst",
    });

    expect(created.id).toMatch(/^research-/);
    const list = await repo.list();
    expect(list.some((item) => item.id === created.id)).toBe(true);
    expect(list.find((item) => item.id === created.id)?.name).toBe(
      "Configurable MA Study"
    );
    expect((await repo.getById(created.id))?.runConfiguration).toMatchObject({
      symbol: "QQQ",
      shortWindow: 10,
      longWindow: 50,
      transactionCost: 0.002,
    });
  });

  it("rejects invalid executable definitions before persistence", async () => {
    const repo = new LocalResearchRepository();
    await expect(
      repo.create({
        name: "Invalid windows",
        researchQuestion: "Will this run?",
        symbol: "SPY",
        benchmark: "SPY",
        startDate: "2024-01-01",
        endDate: "2025-01-01",
        shortWindow: 60,
        longWindow: 20,
        transactionCost: 0.001,
        tags: [],
        owner: "Analyst",
      })
    ).rejects.toThrow("Long MA window");
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
