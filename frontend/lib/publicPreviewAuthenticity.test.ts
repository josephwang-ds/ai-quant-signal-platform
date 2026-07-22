import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { createElement } from "react";
import RiskGateReview from "@/components/features/risk/RiskGateReview";
import { CANONICAL_MA_CROSSOVER } from "@/lib/canonicalMaCrossover";

/**
 * PR-011A — Removes the fabricated evidence that used to live in
 * `frontend/lib/mockQuantData.ts`.
 *
 * Risk Gate Review is now a live Risk Review module that calls
 * `/api/v1/risk/review`. These tests still prove fabricated numbers are gone
 * from the production path, and that the form renders without inventing evidence.
 */

const FABRICATED_NUMERIC_STRINGS = [
  "1.12", // fabricated Sharpe ratio
  "-8.6", // fabricated max drawdown
  "8.6%",
  "0.58", // fabricated hit rate
  "76/100",
  "76 / 100", // fabricated Strategy Health Score
  "78/100",
  "72/100",
  "70/100",
  "74/100", // fabricated pillar scores
];

const FABRICATED_VERDICT_STRINGS = [
  "Approved with caution",
  "Approved — size capped",
  "Downgraded to WATCH",
];

const PANELS: Array<{ name: string; render: () => ReturnType<typeof render> }> = [
  {
    name: "RiskGateReview",
    render: () => render(createElement(RiskGateReview)),
  },
];

function collectProductionFiles(root: string): string[] {
  const out: string[] = [];
  function walk(dir: string) {
    for (const entry of readdirSync(dir)) {
      if (
        entry === "node_modules" ||
        entry === ".next" ||
        entry === "coverage" ||
        entry === "dist" ||
        entry === "__tests__" ||
        entry === "tests"
      ) {
        continue;
      }
      const full = join(dir, entry);
      const st = statSync(full);
      if (st.isDirectory()) {
        walk(full);
        continue;
      }
      if (
        /\.(ts|tsx)$/.test(entry) &&
        !/\.(test|spec)\.(ts|tsx)$/.test(entry)
      ) {
        out.push(full);
      }
    }
  }
  walk(root);
  return out;
}

describe("PR-011A authenticity — mockQuantData is fully removed", () => {
  it("no longer exists on disk", () => {
    const projectRoot = join(process.cwd());
    expect(existsSync(join(projectRoot, "lib", "mockQuantData.ts"))).toBe(false);
  });

  it("is not imported by any production file under app/ or components/", () => {
    const projectRoot = join(process.cwd());
    const files = [
      ...collectProductionFiles(join(projectRoot, "app")),
      ...collectProductionFiles(join(projectRoot, "components")),
    ];
    expect(files.length).toBeGreaterThan(0);

    const importers = files.filter((file) =>
      readFileSync(file, "utf8").includes("mockQuantData")
    );
    expect(importers).toEqual([]);
  });

  it("the removed executive cockpit dead-code components no longer exist", () => {
    const projectRoot = join(process.cwd());
    expect(
      existsSync(
        join(
          projectRoot,
          "components",
          "features",
          "executive",
          "ExecutiveCockpitGrid.tsx"
        )
      )
    ).toBe(false);
    expect(
      existsSync(
        join(
          projectRoot,
          "components",
          "features",
          "executive",
          "ExecutiveCockpitSnapshot.tsx"
        )
      )
    ).toBe(false);
    expect(
      existsSync(join(projectRoot, "components", "features", "executive"))
    ).toBe(false);
    expect(
      existsSync(join(projectRoot, "components", "features", "decision-room"))
    ).toBe(false);
  });
});

describe("PR-011A authenticity — repository-wide fabricated-evidence scan", () => {
  it("finds zero fabricated numeric evidence in app/ or components/ (excluding tests)", () => {
    const projectRoot = join(process.cwd());
    const files = [
      ...collectProductionFiles(join(projectRoot, "app")),
      ...collectProductionFiles(join(projectRoot, "components")),
    ];

    const hits: string[] = [];
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      for (const needle of [...FABRICATED_NUMERIC_STRINGS, ...FABRICATED_VERDICT_STRINGS]) {
        if (text.includes(needle)) {
          hits.push(`${file}: ${needle}`);
        }
      }
    }
    expect(hits).toEqual([]);
  });

  it("finds zero fabricated 'Approved with caution' / 'Approved — size capped' governance verdicts anywhere in lib/", () => {
    const projectRoot = join(process.cwd());
    const files = collectProductionFiles(join(projectRoot, "lib"));

    const hits: string[] = [];
    for (const file of files) {
      const text = readFileSync(file, "utf8");
      for (const needle of FABRICATED_VERDICT_STRINGS) {
        if (text.includes(needle)) {
          hits.push(`${file}: ${needle}`);
        }
      }
    }
    expect(hits).toEqual([]);
  });
});

describe("PR-011A authenticity — Risk Review form does not invent evidence", () => {
  for (const panel of PANELS) {
    it(`${panel.name} renders no fabricated numeric or BUY/SELL/Approved evidence`, () => {
      panel.render();

      for (const needle of FABRICATED_NUMERIC_STRINGS) {
        expect(screen.queryByText(needle)).toBeNull();
      }
      for (const needle of FABRICATED_VERDICT_STRINGS) {
        expect(screen.queryByText(needle)).toBeNull();
      }
      expect(screen.queryByText("BUY")).toBeNull();
      expect(screen.queryByText("SELL")).toBeNull();
    });

    it(`${panel.name} renders the live Risk Review form, not a fabricated scorecard`, () => {
      panel.render();

      expect(screen.getByText("Risk Review")).toBeInTheDocument();
      expect(screen.getByText("Run Risk Review")).toBeInTheDocument();
      expect(screen.queryByText("Planned capabilities")).toBeNull();
      expect(screen.queryByText("76/100")).toBeNull();
    });
  }
});

describe("PR-011A authenticity — canonical research path is unaffected", () => {
  it("keeps the canonical MA Crossover definition free of invented evidence", () => {
    expect(CANONICAL_MA_CROSSOVER.definition.symbol).toBe("SPY");
    expect(CANONICAL_MA_CROSSOVER.definition.benchmark).toBe("SPY Buy & Hold");
    expect(CANONICAL_MA_CROSSOVER.runtimeMarketData).toBeNull();
    expect(CANONICAL_MA_CROSSOVER.calculatedEvidence).toBeNull();
    expect(CANONICAL_MA_CROSSOVER.evaluationResult).toBeNull();
  });
});
