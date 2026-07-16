import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import ResearchValidationPanel, {
  type ResearchValidationLabels,
} from "@/components/features/research/validation/ResearchValidationPanel";
import LoadingState from "@/components/ui/LoadingState";
import {
  ResearchValidationApiError,
  fetchResearchValidation,
} from "@/lib/researchValidationApi";
import type { ExecutionMetrics } from "@/types/researchExecution";
import type { ResearchValidationResult } from "@/types/researchValidation";

const metrics: ExecutionMetrics = {
  total_return: 0.12,
  cagr: 0.05,
  annualized_volatility: 0.14,
  sharpe_ratio: 0.61,
  maximum_drawdown: -0.18,
  trade_count: 11,
  win_rate: null,
  turnover: 10,
  total_transaction_costs: 0.011,
  observation_count: 800,
  start_date: "2018-03-01",
  end_date: "2021-06-30",
};

const provenance = {
  provider: "yahoo",
  symbol: "SPY",
  source: "Yahoo Finance via yfinance",
  retrieved_at: "2026-07-14T01:00:00Z",
  requested_start: "2018-01-01",
  requested_end: null,
  actual_start: "2018-01-02",
  actual_end: "2026-07-13",
  interval: "1d",
  cache_hit: true,
  cache_stale: false,
  currency: "USD",
};

const stages = [
  "historical_backtest",
  "benchmark_comparison",
  "out_of_sample",
  "parameter_sensitivity",
  "transaction_cost_sensitivity",
  "data_quality",
].map((stage, index) => ({
  stage,
  label: stage.replaceAll("_", " "),
  status: index === 2 ? ("incomplete" as const) : ("completed" as const),
  summary: index === 2 ? "OOS evidence is partial." : `${stage} evidence returned.`,
  evidence: { observation_count: 800 },
  rules: ["Use backend-derived evidence."],
  warnings: index === 2 ? ["OOS sample is below the preferred size."] : [],
  blockers: index === 2 ? ["More OOS observations required."] : [],
  generated_at: "2026-07-14T01:01:00Z",
  provenance,
}));

const SAMPLE_VALIDATION: ResearchValidationResult = {
  research_id: "ma-crossover-spy",
  strategy: { short_window: 20, long_window: 60 },
  provenance,
  validation_status: "incomplete",
  evidence_complete: false,
  stages,
  oos: {
    status: "incomplete",
    split_date: "2023-11-17",
    in_sample_ratio: 0.7,
    minimum_oos_observations: 252,
    in_sample_metrics: metrics,
    out_of_sample_metrics: { ...metrics, total_return: 0.03 },
    oos_benchmark_metrics: { ...metrics, total_return: 0.08 },
    in_sample_observation_count: 1000,
    out_of_sample_observation_count: 240,
    warnings: ["OOS sample is below the preferred size."],
    boundary_convention: "IS ends before split date; OOS begins on split date.",
  },
  parameter_sensitivity: {
    status: "completed",
    results: [
      {
        short_window: 10,
        long_window: 50,
        total_return: 0.2,
        cagr: 0.07,
        sharpe_ratio: 0.8,
        maximum_drawdown: -0.2,
        annualized_volatility: 0.16,
        trade_count: 15,
        total_transaction_costs: 0.015,
        status: "completed",
        warnings: [],
        is_canonical: false,
      },
      {
        short_window: 20,
        long_window: 60,
        total_return: 0.12,
        cagr: 0.05,
        sharpe_ratio: 0.61,
        maximum_drawdown: -0.18,
        annualized_volatility: 0.14,
        trade_count: 11,
        total_transaction_costs: 0.011,
        status: "completed",
        warnings: [],
        is_canonical: true,
      },
    ],
    valid_combination_count: 2,
    profitable_combination_count: 2,
    positive_sharpe_count: 2,
    median_sharpe: 0.705,
    sharpe_range: [0.61, 0.8],
    median_max_drawdown: -0.19,
    canonical_percentile_by_sharpe: 0.5,
    warnings: [],
  },
  transaction_cost_sensitivity: {
    status: "completed",
    results: [
      {
        transaction_cost: 0,
        total_return: 0.15,
        cagr: 0.06,
        sharpe_ratio: 0.7,
        maximum_drawdown: -0.18,
        trade_count: 11,
        total_transaction_costs: 0,
        return_degradation_from_zero: 0,
        sharpe_degradation_from_zero: 0,
        mathematically_valid: true,
        warnings: [],
      },
      {
        transaction_cost: 0.001,
        total_return: 0.12,
        cagr: 0.05,
        sharpe_ratio: 0.61,
        maximum_drawdown: -0.18,
        trade_count: 11,
        total_transaction_costs: 0.011,
        return_degradation_from_zero: 0.03,
        sharpe_degradation_from_zero: 0.09,
        mathematically_valid: true,
        warnings: [],
      },
    ],
    canonical_cost: 0.001,
    canonical_cost_result: null,
    warnings: [],
  },
  data_quality: {
    status: "completed",
    fatal_issues: [],
    warnings: ["One provider warning retained."],
    informational: {
      duplicate_dates: 0,
      notes: [
        "Yahoo prices use yfinance auto_adjust (auto_adjust).",
      ],
    },
    checks: [
      {
        name: "Unique dates",
        severity: "fatal",
        status: "passed",
        summary: "No duplicate dates.",
      },
    ],
  },
  warnings: ["Validation is incomplete."],
  generated_at: "2026-07-14T01:02:00Z",
  validation_run_id: "val-sample-run-id",
};

const labels: ResearchValidationLabels = {
  title: "Validation",
  summary: "Backend-derived validation evidence.",
  status: "Status",
  evidenceComplete: "Evidence complete",
  yes: "Yes",
  no: "No",
  completed: "Completed",
  incomplete: "Incomplete",
  failed: "Failed",
  unavailable: "Unavailable",
  source: "Source",
  generated: "Generated",
  rules: "Rules",
  warnings: "Warnings",
  dataNotes: "Data notes",
  blockers: "Blockers",
  evidence: "Evidence",
  oosTitle: "Out-of-sample validation",
  splitDate: "Exact split date",
  inSampleRatio: "In-sample ratio",
  minimumOos: "Minimum OOS observations",
  boundary: "Boundary convention",
  inSample: "In sample",
  outOfSample: "Out of sample",
  benchmark: "OOS benchmark",
  observations: "observations",
  metric: "Metric",
  totalReturn: "Total return",
  cagr: "CAGR",
  sharpe: "Sharpe ratio",
  maxDrawdown: "Maximum drawdown",
  volatility: "Annualized volatility",
  trades: "Trade count",
  totalCosts: "Total transaction costs",
  parameterTitle: "Parameter sensitivity",
  validCombinations: "Valid combinations",
  profitableCombinations: "Profitable combinations",
  positiveSharpe: "Positive Sharpe combinations",
  medianSharpe: "Median Sharpe",
  sharpeRange: "Sharpe range",
  medianDrawdown: "Median maximum drawdown",
  canonicalPercentile: "Canonical Sharpe percentile",
  shortWindow: "Short window",
  longWindow: "Long window",
  canonical: "Canonical",
  costTitle: "Transaction-cost sensitivity",
  transactionCost: "Transaction cost",
  returnDegradation: "Return degradation from zero",
  sharpeDegradation: "Sharpe degradation from zero",
  mathematicallyValid: "Mathematically valid",
  canonicalCost: "Canonical cost",
  dataQualityTitle: "Data quality",
  provider: "Provider",
  dateRange: "Actual date range",
  cache: "Cache",
  cacheHit: "Cache hit",
  cacheMiss: "Cache miss",
  fatalIssues: "Fatal issues",
  checks: "Data-quality checks",
  check: "Check",
  severity: "Severity",
  details: "Details",
  notAvailable: "n/a",
};

describe("ResearchValidationPanel", () => {
  it("shows reviewer-facing evidence and the exact OOS split without raw stage JSON", () => {
    render(<ResearchValidationPanel validation={SAMPLE_VALIDATION} labels={labels} language="en" />);

    expect(screen.getByText("2023-11-17")).toBeInTheDocument();
    expect(screen.getByText(/IS ends before split date/)).toBeInTheDocument();
    expect(screen.getAllByText("Incomplete").length).toBeGreaterThan(1);
    expect(screen.queryByText("More OOS observations required.")).not.toBeInTheDocument();
    expect(screen.queryByText(/observation_count/)).not.toBeInTheDocument();
  });

  it("highlights only the backend-marked canonical sensitivity row", () => {
    const { container } = render(
      <ResearchValidationPanel validation={SAMPLE_VALIDATION} labels={labels} language="en" />
    );

    const canonicalRows = container.querySelectorAll("tr.is-canonical");
    expect(canonicalRows).toHaveLength(1);
    expect(canonicalRows[0]).toHaveTextContent("20");
    expect(canonicalRows[0]).toHaveTextContent("60");
    expect(canonicalRows[0]).toHaveTextContent("Canonical");
  });

  it("renders backend cost degradation and data-quality warnings", () => {
    render(<ResearchValidationPanel validation={SAMPLE_VALIDATION} labels={labels} language="en" />);

    expect(screen.getAllByText("3.00%").length).toBeGreaterThan(0);
    expect(screen.getByText("One provider warning retained.")).toBeInTheDocument();
    expect(
      screen.getAllByText(/Yahoo Finance via yfinance/).length
    ).toBeGreaterThan(0);
    expect(screen.getByText("Fatal issues")).toBeInTheDocument();
  });

  it("does not render research confidence", () => {
    render(<ResearchValidationPanel validation={SAMPLE_VALIDATION} labels={labels} language="en" />);
    expect(screen.queryByText(/confidence/i)).not.toBeInTheDocument();
  });

  it("shows a loading state without completed mock statuses", () => {
    render(<LoadingState message="Loading validation evidence from backend…" />);
    expect(screen.getByText("Loading validation evidence from backend…")).toBeInTheDocument();
    expect(screen.queryByText("Completed")).not.toBeInTheDocument();
  });
});

describe("researchValidationApi", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("uses the validation endpoint and returns backend success", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => SAMPLE_VALIDATION,
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchResearchValidation()).resolves.toEqual(SAMPLE_VALIDATION);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/research/validation",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("surfaces backend provider errors without fallback evidence", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: false,
        status: 502,
        json: async () => ({ detail: "Market data provider unavailable" }),
      }))
    );

    await expect(fetchResearchValidation()).rejects.toBeInstanceOf(
      ResearchValidationApiError
    );
    await expect(fetchResearchValidation()).rejects.toMatchObject({
      status: 502,
      message: "Market data provider unavailable",
    });
  });
});
