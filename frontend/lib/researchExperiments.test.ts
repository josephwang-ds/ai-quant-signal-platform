import { describe, expect, it } from "vitest";
import {
  getMockExperimentById,
  getMockExperiments,
} from "@/lib/mockExperimentCatalog";
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
  it("provides a coherent six-experiment story for momentum research", () => {
    const experiments = getMockExperiments("rs-momentum-001");
    expect(experiments).toHaveLength(6);
    expect(experiments.map((item) => item.name)).toEqual(
      expect.arrayContaining([
        "MA 20/60 baseline",
        "MA 10/50 parameter variant",
        "RSI-filtered crossover",
        "Transaction-cost stress test",
        "Out-of-sample 2022–2025 walk-forward",
        "Sideways-market regime test",
      ])
    );
  });

  it("selects experiment by id within research", () => {
    const found = getMockExperimentById("rs-momentum-001", "exp-mom-001");
    expect(found?.name).toBe("MA 20/60 baseline");
    expect(getMockExperimentById("rs-momentum-001", "missing")).toBeNull();
  });
});

describe("filterAndSortExperiments", () => {
  const experiments = getMockExperiments("rs-momentum-001");

  it("filters by status and type", () => {
    const byStatus = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      status: "Completed",
    });
    expect(byStatus.every((item) => item.status === "Completed")).toBe(true);

    const byType = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      experimentType: "Cost Test",
    });
    expect(byType).toHaveLength(1);
    expect(byType[0].name).toBe("Transaction-cost stress test");
  });

  it("sorts by sharpe when result sort is selected", () => {
    const sorted = filterAndSortExperiments(experiments, {
      ...DEFAULT_EXPERIMENT_FILTERS,
      sort: "result",
    });
    const sharpes = sorted
      .map((item) => item.metrics.sharpe)
      .filter((value): value is number => value !== null);
    expect(sharpes[0]).toBeGreaterThanOrEqual(sharpes[sharpes.length - 1]);
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
    expect(countActiveExperiments(getMockExperiments("rs-momentum-001"))).toBe(
      2
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
      researchId: "rs-momentum-001",
      owner: "A. Chen",
      values: {
        name: "Local draft",
        hypothesis: "H",
        experimentType: "Backtest",
        datasetOrSymbol: "Panel",
        startDate: "2020-01-01",
        endDate: "2021-01-01",
        benchmark: "B&H",
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
