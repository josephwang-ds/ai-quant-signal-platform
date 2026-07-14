import { describe, expect, it } from "vitest";
import {
  getMockExperimentById,
  getMockExperiments,
} from "@/lib/mockExperimentCatalog";
import { CANONICAL_RESEARCH_ID } from "@/lib/mockResearchCatalog";
import {
  countActiveExperiments,
  createLocalExperiment,
  createNotebookEntryFromExperiment,
  createTimelineEventFromExperiment,
  filterAndSortExperiments,
  getExperimentLifecycleStepState,
  hasExperimentComposerErrors,
  validateExperimentComposer,
} from "@/lib/researchExperiments";
import { DEFAULT_EXPERIMENT_FILTERS } from "@/types/experiment";

describe("experiment catalog", () => {
  it("lists planned MA crossover experiments without metrics", () => {
    const experiments = getMockExperiments(CANONICAL_RESEARCH_ID);
    expect(experiments).toHaveLength(5);
    expect(experiments.every((item) => item.status === "Designed")).toBe(true);
    expect(experiments.every((item) => item.metrics.sharpe === null)).toBe(true);
    expect(experiments.map((item) => item.name)).toEqual(
      expect.arrayContaining([
        "MA20/60 Baseline Backtest — Planned",
        "Chronological OOS Validation — Planned",
        "Parameter Sensitivity Grid — Planned",
        "Transaction-Cost Review — Planned",
        "Regime Analysis — Planned",
      ])
    );
  });

  it("selects experiment by id within research", () => {
    const found = getMockExperimentById(CANONICAL_RESEARCH_ID, "exp-ma-baseline");
    expect(found?.name).toContain("Baseline");
    expect(getMockExperimentById(CANONICAL_RESEARCH_ID, "missing")).toBeNull();
  });
});

describe("filterAndSortExperiments", () => {
  const experiments = getMockExperiments(CANONICAL_RESEARCH_ID);

  it("filters by status and type", () => {
    const byStatus = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      status: "Designed",
    });
    expect(byStatus).toHaveLength(5);

    const byType = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      experimentType: "Cost Test",
    });
    expect(byType).toHaveLength(1);
  });
});

describe("experiment lifecycle helpers", () => {
  it("marks completed/current/upcoming on the main path", () => {
    expect(getExperimentLifecycleStepState("Designed", "Running")).toBe(
      "completed"
    );
    expect(getExperimentLifecycleStepState("Running", "Running")).toBe("current");
    expect(getExperimentLifecycleStepState("Completed", "Running")).toBe(
      "upcoming"
    );
  });

  it("counts active experiments", () => {
    expect(countActiveExperiments(getMockExperiments(CANONICAL_RESEARCH_ID))).toBe(
      5
    );
  });
});

describe("validateExperimentComposer", () => {
  const messages = {
    nameRequired: "name",
    hypothesisRequired: "hypothesis",
    typeRequired: "type",
    datasetRequired: "dataset",
    startRequired: "start",
    endRequired: "end",
    dateRangeInvalid: "range",
    successRequired: "success",
    falsificationRequired: "falsify",
  };

  it("requires core fields and valid date range", () => {
    const errors = validateExperimentComposer(
      {
        name: "",
        hypothesis: "",
        experimentType: "",
        datasetOrSymbol: "",
        startDate: "2024-01-01",
        endDate: "2023-01-01",
        benchmark: "",
        parameters: "",
        successCriteria: "",
        falsificationCondition: "",
        notes: "",
      },
      messages
    );
    expect(hasExperimentComposerErrors(errors)).toBe(true);
    expect(errors.dateRange).toBe("range");
  });

  it("passes when required fields are valid", () => {
    const errors = validateExperimentComposer(
      {
        name: "Test",
        hypothesis: "H",
        experimentType: "Backtest",
        datasetOrSymbol: "SPY",
        startDate: "2020-01-01",
        endDate: "2021-01-01",
        benchmark: "B&H",
        parameters: "fast=20",
        successCriteria: "document results",
        falsificationCondition: "protocol unreproducible",
        notes: "",
      },
      messages
    );
    expect(hasExperimentComposerErrors(errors)).toBe(false);
  });
});

describe("local experiment integration", () => {
  it("creates Designed experiment plus notebook and timeline artifacts", () => {
    const experiment = createLocalExperiment({
      researchId: CANONICAL_RESEARCH_ID,
      owner: "Research Workspace",
      values: {
        name: "Local draft",
        hypothesis: "H",
        experimentType: "Backtest",
        datasetOrSymbol: "SPY",
        startDate: "2020-01-01",
        endDate: "2021-01-01",
        benchmark: "SPY Buy & Hold",
        parameters: "a=1",
        successCriteria: "ok",
        falsificationCondition: "fail",
        notes: "n",
      },
      now: "2026-07-14T13:00:00.000Z",
    });
    expect(experiment.status).toBe("Designed");

    const note = createNotebookEntryFromExperiment(experiment);
    expect(note.entryType).toBe("Decision");
    expect(note.relatedArtifact?.kind).toBe("experiment");

    const event = createTimelineEventFromExperiment(experiment);
    expect(event.kind).toBe("experiment");
    expect(event.title).toContain("ExperimentDesigned");
  });
});
