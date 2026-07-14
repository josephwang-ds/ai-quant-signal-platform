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
  it("provides the single MA crossover baseline experiment", () => {
    const experiments = getMockExperiments(CANONICAL_RESEARCH_ID);
    expect(experiments).toHaveLength(1);
    expect(experiments[0].name).toBe("MA 20/60 baseline — SPY");
    expect(experiments[0].datasetOrSymbol).toBe("SPY");
    expect(experiments[0].benchmark).toBe("SPY Buy & Hold");
    expect(experiments[0].metrics.sharpe).toBeNull();
  });

  it("selects experiment by id within research", () => {
    const found = getMockExperimentById(CANONICAL_RESEARCH_ID, "exp-ma-001");
    expect(found?.name).toBe("MA 20/60 baseline — SPY");
    expect(getMockExperimentById(CANONICAL_RESEARCH_ID, "missing")).toBeNull();
  });

  it("returns an empty catalog for unknown research ids", () => {
    expect(getMockExperiments("rs-fictional-999")).toEqual([]);
  });
});

describe("filterAndSortExperiments", () => {
  const experiments = getMockExperiments(CANONICAL_RESEARCH_ID);

  it("filters by status and type", () => {
    const byStatus = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      status: "Approved",
    });
    expect(byStatus).toHaveLength(1);

    const byType = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      experimentType: "Cost Test",
    });
    expect(byType).toHaveLength(0);
  });

  it("keeps pending metrics null under result sort", () => {
    const sorted = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      sort: "result",
    });
    expect(sorted.every((item) => item.metrics.sharpe === null)).toBe(true);
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
      1
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
        successCriteria: "Sharpe > 0.5",
        falsificationCondition: "Sharpe < 0.2",
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
      owner: "Research Desk",
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
      now: "2026-07-13T13:00:00.000Z",
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
