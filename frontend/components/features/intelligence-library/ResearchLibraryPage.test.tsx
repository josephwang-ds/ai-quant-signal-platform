import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ResearchLibraryPage from "@/components/features/intelligence-library/ResearchLibraryPage";
import { IntelligenceApiError } from "@/lib/intelligence/api";
import type { ResearchRunDetailDto, ResearchRunSummaryDto } from "@/lib/intelligence/types";

const listPublishedRuns = vi.fn();
const getLatestPublishedRun = vi.fn();

vi.mock("@/lib/intelligence/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/intelligence/api")>();
  return {
    ...actual,
    listPublishedRuns: (...args: unknown[]) => listPublishedRuns(...args),
    getLatestPublishedRun: (...args: unknown[]) => getLatestPublishedRun(...args),
  };
});

vi.mock("@/lib/useWorkspaceLanguage", () => ({
  useWorkspaceLanguage: () => ({
    language: "en" as const,
    setLanguage: vi.fn(),
    tr: (key: string) => key,
  }),
}));

vi.mock("@/components/layout/AppShell", () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-shell">{children}</div>
  ),
}));

function summary(
  partial: Partial<ResearchRunSummaryDto> & Pick<ResearchRunSummaryDto, "run_id">
): ResearchRunSummaryDto {
  return {
    run_type: "TREND",
    status: "PUBLISHED",
    created_at: "2026-07-28T04:15:30Z",
    updated_at: "2026-07-28T04:15:30Z",
    published_at: "2026-07-28T04:15:30Z",
    universe: "AAPL, MSFT",
    dataset_version: null,
    feature_version: null,
    model_version: null,
    git_commit: null,
    artifact_count: 2,
    snapshot_count: 1,
    ...partial,
  };
}

function detail(
  partial: Partial<ResearchRunDetailDto> & Pick<ResearchRunDetailDto, "run_id">
): ResearchRunDetailDto {
  return {
    ...summary(partial),
    generator: null,
    environment: null,
    random_seed: null,
    training_window: null,
    prediction_window: null,
    notes: null,
    validation: { ok: true, checks: [] },
    errors: [],
    artifacts: [],
    snapshots: [],
    ...partial,
  };
}

describe("ResearchLibraryPage", () => {
  beforeEach(() => {
    listPublishedRuns.mockReset();
    getLatestPublishedRun.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("loads list and latest in parallel and renders published runs", async () => {
    listPublishedRuns.mockResolvedValue({
      items: [
        summary({
          run_id: "run_20260728T041530Z_a1b2c3d4",
          published_at: "2026-07-28T04:15:30Z",
        }),
        summary({
          run_id: "run_20260729T041530Z_bbbbbbbb",
          run_type: "FACTOR",
          published_at: "2026-07-29T04:15:30Z",
          universe: "US Large Cap",
        }),
      ],
      count: 2,
    });
    getLatestPublishedRun.mockResolvedValue(
      detail({
        run_id: "run_20260729T041530Z_bbbbbbbb",
        run_type: "FACTOR",
        published_at: "2026-07-29T04:15:30Z",
        universe: "US Large Cap",
      })
    );

    render(<ResearchLibraryPage />);

    expect(screen.getByTestId("research-library-loading")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("published-runs-section")).toBeInTheDocument();
    });

    expect(listPublishedRuns).toHaveBeenCalledWith({ status: "PUBLISHED" });
    expect(getLatestPublishedRun).toHaveBeenCalled();
    expect(screen.getByRole("heading", { name: "Research Library" })).toBeInTheDocument();
    expect(screen.getByTestId("latest-published-section")).toBeInTheDocument();
    expect(screen.getByTestId("open-latest-research")).toHaveAttribute(
      "href",
      "/research/run_20260729T041530Z_bbbbbbbb"
    );

    const cards = screen.getAllByTestId("published-run-card");
    expect(cards).toHaveLength(2);
    expect(cards[0]).toHaveAttribute("data-run-id", "run_20260729T041530Z_bbbbbbbb");
    expect(
      within(cards[0]).getByRole("link", {
        name: /Open published research Factor Research · US Large Cap/i,
      })
    ).toHaveAttribute("href", "/research/run_20260729T041530Z_bbbbbbbb");
    expect(screen.getByTestId("research-library-disclaimer")).toBeInTheDocument();
    expect(screen.queryByText(/Phase 4.6A/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Trend Following Study")).not.toBeInTheDocument();
    expect(screen.queryByText(/Sharpe/i)).not.toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("hides latest on latest_missing while preserving the list", async () => {
    listPublishedRuns.mockResolvedValue({
      items: [summary({ run_id: "run_20260728T041530Z_a1b2c3d4" })],
      count: 1,
    });
    getLatestPublishedRun.mockRejectedValue(
      new IntelligenceApiError({
        category: "not_found",
        transportCode: "HTTP_404",
        status: 404,
        backend: {
          error_code: "LATEST_NOT_FOUND",
          message: "no latest published research run",
        },
      })
    );

    render(<ResearchLibraryPage />);

    await waitFor(() => {
      expect(screen.getByTestId("published-runs-section")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("latest-published-section")).not.toBeInTheDocument();
    expect(screen.queryByTestId("research-library-error")).not.toBeInTheDocument();
  });

  it("keeps the list when latest fails with a backend error", async () => {
    listPublishedRuns.mockResolvedValue({
      items: [summary({ run_id: "run_20260728T041530Z_a1b2c3d4" })],
      count: 1,
    });
    getLatestPublishedRun.mockRejectedValue(
      new IntelligenceApiError({
        category: "backend_unavailable",
        transportCode: "HTTP_503",
        status: 503,
        backend: {
          error_code: "INTELLIGENCE_STORAGE_ERROR",
          message: "storage unavailable",
        },
      })
    );

    render(<ResearchLibraryPage />);

    await waitFor(() => {
      expect(screen.getByTestId("published-runs-section")).toBeInTheDocument();
    });
    expect(screen.getByTestId("latest-unavailable-note")).toBeInTheDocument();
  });

  it("shows page-level error and retries both requests", async () => {
    const user = userEvent.setup();
    listPublishedRuns.mockRejectedValue(
      new IntelligenceApiError({
        category: "backend_unavailable",
        transportCode: "HTTP_503",
        status: 503,
        backend: {
          error_code: "INTELLIGENCE_STORAGE_ERROR",
          message: "storage unavailable",
        },
      })
    );
    getLatestPublishedRun.mockRejectedValue(
      new IntelligenceApiError({
        category: "backend_unavailable",
        transportCode: "HTTP_503",
        status: 503,
      })
    );

    render(<ResearchLibraryPage />);

    await waitFor(() => {
      expect(screen.getByTestId("research-library-error")).toBeInTheDocument();
    });

    listPublishedRuns.mockResolvedValue({ items: [], count: 0 });
    getLatestPublishedRun.mockRejectedValue(
      new IntelligenceApiError({
        category: "not_found",
        transportCode: "HTTP_404",
        status: 404,
        backend: {
          error_code: "LATEST_NOT_FOUND",
          message: "no latest",
        },
      })
    );

    await user.click(screen.getByTestId("research-library-retry"));

    await waitFor(() => {
      expect(screen.getByTestId("research-library-empty")).toBeInTheDocument();
    });
    expect(listPublishedRuns).toHaveBeenCalledTimes(2);
    expect(getLatestPublishedRun).toHaveBeenCalledTimes(2);
    expect(screen.getByTestId("open-research-engine")).toHaveAttribute(
      "href",
      "/engine"
    );
  });

  it("treats latest-with-empty-list as inconsistent and offers retry", async () => {
    listPublishedRuns.mockResolvedValue({ items: [], count: 0 });
    getLatestPublishedRun.mockResolvedValue(
      detail({ run_id: "run_20260728T041530Z_a1b2c3d4" })
    );

    render(<ResearchLibraryPage />);

    await waitFor(() => {
      expect(screen.getByTestId("research-library-error")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("latest-published-section")).not.toBeInTheDocument();
    expect(screen.getByText(/list is empty while a latest published run/i)).toBeInTheDocument();
  });

  it("filters by run type without inventing status filters", async () => {
    const user = userEvent.setup();
    listPublishedRuns.mockResolvedValue({
      items: [
        summary({ run_id: "run_trend", run_type: "TREND" }),
        summary({
          run_id: "run_factor",
          run_type: "FACTOR",
          published_at: "2026-07-29T04:15:30Z",
        }),
      ],
      count: 2,
    });
    getLatestPublishedRun.mockResolvedValue(
      detail({ run_id: "run_factor", run_type: "FACTOR" })
    );

    render(<ResearchLibraryPage />);

    await waitFor(() => {
      expect(screen.getByTestId("run-type-filter")).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/status/i)).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Run type"), "FACTOR");
    expect(screen.getAllByTestId("published-run-card")).toHaveLength(1);
    expect(screen.getByTestId("published-run-card")).toHaveAttribute(
      "data-run-id",
      "run_factor"
    );

    await user.selectOptions(screen.getByLabelText("Run type"), "all");
    expect(screen.getAllByTestId("published-run-card")).toHaveLength(2);
  });

  it("does not use local catalog or demo fallback sources", async () => {
    const { readFileSync } = await import("node:fs");
    const { join } = await import("node:path");
    const pageSource = readFileSync(
      join(process.cwd(), "components/features/intelligence-library/ResearchLibraryPage.tsx"),
      "utf8"
    );
    const hookSource = readFileSync(
      join(process.cwd(), "lib/intelligence/usePublishedRuns.ts"),
      "utf8"
    );
    expect(pageSource).not.toContain("localResearchRepository");
    expect(pageSource).not.toContain("mockResearchCatalog");
    expect(hookSource).not.toMatch(/DEMO_MODE|demoRuns|mockPublished/i);
    expect(hookSource).toContain("listPublishedRuns");
    expect(hookSource).toContain("getLatestPublishedRun");
  });
});
