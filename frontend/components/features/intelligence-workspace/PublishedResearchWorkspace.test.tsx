import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import PublishedResearchWorkspace from "@/components/features/intelligence-workspace/PublishedResearchWorkspace";
import { IntelligenceApiError } from "@/lib/intelligence/api";
import type {
  ArtifactReferenceDto,
  ResearchRunDetailDto,
  ResearchSummarySnapshot,
  SignalSnapshot,
  SnapshotContentDto,
  SnapshotReferenceDto,
} from "@/lib/intelligence/types";

const getPublishedRunDetail = vi.fn();
const listPublishedRunArtifacts = vi.fn();
const listPublishedRunSnapshots = vi.fn();
const getPublishedSnapshotContent = vi.fn();

let searchParams = new URLSearchParams();

vi.mock("@/lib/intelligence/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/intelligence/api")>();
  return {
    ...actual,
    getPublishedRunDetail: (...args: unknown[]) => getPublishedRunDetail(...args),
    listPublishedRunArtifacts: (...args: unknown[]) =>
      listPublishedRunArtifacts(...args),
    listPublishedRunSnapshots: (...args: unknown[]) =>
      listPublishedRunSnapshots(...args),
    getPublishedSnapshotContent: (...args: unknown[]) =>
      getPublishedSnapshotContent(...args),
  };
});

vi.mock("next/navigation", () => ({
  useSearchParams: () => searchParams,
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

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

const RUN_ID = "run_20260728T041530Z_a1b2c3d4";

function artifact(
  partial: Partial<ArtifactReferenceDto> & Pick<ArtifactReferenceDto, "artifact_id">
): ArtifactReferenceDto {
  return {
    name: "metrics",
    artifact_type: "factor_metrics",
    schema_version: "v1",
    media_type: "application/json",
    checksum_algorithm: "sha256",
    checksum: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    size_bytes: 2048,
    row_count: 10,
    created_at: "2026-07-28T04:15:30Z",
    ...partial,
  };
}

function snapshot(
  partial: Partial<SnapshotReferenceDto> &
    Pick<SnapshotReferenceDto, "snapshot_id" | "snapshot_type">
): SnapshotReferenceDto {
  return {
    name: partial.snapshot_type,
    schema_version:
      partial.snapshot_type === "signal"
        ? "signal-snapshot/v1"
        : "research-summary-snapshot/v1",
    media_type: "application/json",
    checksum_algorithm: "sha256",
    checksum: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    size_bytes: 1024,
    created_at: "2026-07-28T04:20:00Z",
    as_of: "2026-07-28T00:00:00Z",
    source_artifact_ids: ["art_1"],
    ...partial,
  };
}

function detail(
  partial: Partial<ResearchRunDetailDto> = {}
): ResearchRunDetailDto {
  return {
    run_id: RUN_ID,
    run_type: "FACTOR",
    status: "PUBLISHED",
    created_at: "2026-07-28T04:15:30Z",
    updated_at: "2026-07-28T04:15:30Z",
    published_at: "2026-07-28T04:15:30Z",
    universe: "AAPL, MSFT",
    dataset_version: "ds_v1",
    feature_version: "feat_v1",
    model_version: null,
    git_commit: "abc1234",
    artifact_count: 1,
    snapshot_count: 2,
    generator: "builder",
    environment: "test",
    random_seed: 7,
    training_window: "2024",
    prediction_window: "2025",
    notes: null,
    validation: { ok: true, checks: ["schema_ok", "checksum_recorded"] },
    errors: [],
    artifacts: [],
    snapshots: [],
    ...partial,
  };
}

function summaryContent(
  overrides: Partial<ResearchSummarySnapshot> = {}
): ResearchSummarySnapshot {
  return {
    schema_version: "research-summary-snapshot/v1",
    generated_at: "2026-07-28T04:20:00Z",
    as_of: "2026-07-28T00:00:00Z",
    research_title: "Factor Study",
    research_objective: "Evaluate factor stability",
    run_type: "FACTOR",
    universe: "AAPL, MSFT",
    analysis_window: "2020-2024",
    validation_status: "passed",
    key_findings: [
      { code: "F1", statement: "Factor remains stable", category: "stability" },
    ],
    limitations: [{ code: "L1", statement: "Short sample window" }],
    artifact_summary: [
      { artifact_id: "art_1", name: "metrics", artifact_type: "factor_metrics" },
    ],
    provenance: {
      source_artifact_ids: ["art_1"],
      builder: "summary_builder_v1",
      notes: null,
    },
    ...overrides,
  };
}

function signalContent(
  overrides: Partial<SignalSnapshot> = {}
): SignalSnapshot {
  return {
    schema_version: "signal-snapshot/v1",
    generated_at: "2026-07-28T04:20:00Z",
    as_of: "2026-07-28T00:00:00Z",
    universe: "AAPL, MSFT",
    signals: [
      {
        symbol: "MSFT",
        signal_name: "momentum",
        direction: "positive",
        score: null,
        confidence: null,
        horizon: "20d",
        evidence_artifact_ids: ["art_1"],
        metadata: { secret: "do-not-render" },
      },
      {
        symbol: "AAPL",
        signal_name: "value",
        direction: "strong_negative",
        score: -0.4,
        confidence: 0.7,
        horizon: "20d",
        evidence_artifact_ids: ["art_1"],
        metadata: {},
      },
    ],
    provenance: {
      source_artifact_ids: ["art_1"],
      builder: "signal_builder_v1",
      notes: null,
    },
    ...overrides,
  };
}

function contentDto(
  reference: SnapshotReferenceDto,
  content: ResearchSummarySnapshot | SignalSnapshot
): SnapshotContentDto {
  return { run_id: RUN_ID, reference, content };
}

function mockHappyPath(options?: {
  summary?: ResearchSummarySnapshot | null;
  signal?: SignalSnapshot | null;
  artifactsFail?: boolean;
  run?: Partial<ResearchRunDetailDto>;
}) {
  const summaryRef = snapshot({
    snapshot_id: "snap_summary",
    snapshot_type: "research_summary",
  });
  const signalRef = snapshot({
    snapshot_id: "snap_signal",
    snapshot_type: "signal",
  });

  getPublishedRunDetail.mockResolvedValue(detail(options?.run));
  if (options?.artifactsFail) {
    listPublishedRunArtifacts.mockRejectedValue(
      new IntelligenceApiError({
        category: "backend_unavailable",
        transportCode: "HTTP_503",
        status: 503,
      })
    );
  } else {
    listPublishedRunArtifacts.mockResolvedValue({
      run_id: RUN_ID,
      items: [artifact({ artifact_id: "art_1" })],
      count: 1,
    });
  }
  listPublishedRunSnapshots.mockResolvedValue({
    run_id: RUN_ID,
    items: [summaryRef, signalRef],
    count: 2,
  });

  getPublishedSnapshotContent.mockImplementation(
    async (_runId: string, snapshotId: string) => {
      if (snapshotId === "snap_summary") {
        if (options?.summary === null) {
          throw new IntelligenceApiError({
            category: "unknown",
            transportCode: "INVALID",
          });
        }
        return contentDto(summaryRef, options?.summary ?? summaryContent());
      }
      if (snapshotId === "snap_signal") {
        if (options?.signal === null) {
          throw new IntelligenceApiError({
            category: "unknown",
            transportCode: "INVALID",
          });
        }
        return contentDto(signalRef, options?.signal ?? signalContent());
      }
      throw new IntelligenceApiError({
        category: "not_found",
        transportCode: "HTTP_404",
        status: 404,
        backend: { error_code: "SNAPSHOT_NOT_FOUND", message: "missing" },
      });
    }
  );

  return { summaryRef, signalRef };
}

describe("PublishedResearchWorkspace (Phase 4.6C2)", () => {
  beforeEach(() => {
    searchParams = new URLSearchParams();
    getPublishedRunDetail.mockReset();
    listPublishedRunArtifacts.mockReset();
    listPublishedRunSnapshots.mockReset();
    getPublishedSnapshotContent.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("hard-gates on run detail before artifact/snapshot reference lists", async () => {
    let resolveDetail!: (value: ResearchRunDetailDto) => void;
    getPublishedRunDetail.mockReturnValue(
      new Promise<ResearchRunDetailDto>((resolve) => {
        resolveDetail = resolve;
      })
    );
    listPublishedRunArtifacts.mockResolvedValue({ run_id: RUN_ID, items: [], count: 0 });
    listPublishedRunSnapshots.mockResolvedValue({ run_id: RUN_ID, items: [], count: 0 });

    render(<PublishedResearchWorkspace runId={RUN_ID} />);
    expect(screen.getByTestId("published-workspace-loading")).toBeInTheDocument();
    expect(getPublishedRunDetail).toHaveBeenCalledWith(RUN_ID);
    expect(listPublishedRunArtifacts).not.toHaveBeenCalled();
    expect(listPublishedRunSnapshots).not.toHaveBeenCalled();
    expect(getPublishedSnapshotContent).not.toHaveBeenCalled();

    resolveDetail(detail());
    await waitFor(() => {
      expect(screen.getByTestId("published-workspace-header")).toBeInTheDocument();
    });
    expect(listPublishedRunArtifacts).toHaveBeenCalledWith(RUN_ID);
    expect(listPublishedRunSnapshots).toHaveBeenCalledWith(RUN_ID);
  });

  it("renders not-found, not-published, and unavailable gate states", async () => {
    getPublishedRunDetail.mockRejectedValue(
      new IntelligenceApiError({
        category: "not_found",
        transportCode: "HTTP_404",
        status: 404,
        backend: { error_code: "RUN_NOT_FOUND", message: "missing run" },
      })
    );
    const { rerender } = render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByText("Published research run not found.")).toBeInTheDocument();
    });
    expect(screen.getByTestId("back-to-library")).toHaveAttribute("href", "/");
    expect(listPublishedRunArtifacts).not.toHaveBeenCalled();

    getPublishedRunDetail.mockRejectedValue(
      new IntelligenceApiError({
        category: "invalid_request",
        transportCode: "HTTP_403",
        status: 403,
        backend: {
          error_code: "RUN_NOT_PUBLISHED",
          message: "not published",
        },
      })
    );
    rerender(<PublishedResearchWorkspace runId={`${RUN_ID}_b`} />);
    await waitFor(() => {
      expect(
        screen.getByText("This run is not available as published research.")
      ).toBeInTheDocument();
    });

    getPublishedRunDetail.mockRejectedValue(
      new IntelligenceApiError({
        category: "invalid_request",
        transportCode: "HTTP_400",
        status: 400,
        backend: {
          error_code: "INVALID_RUN_ID",
          message: "bad id",
        },
      })
    );
    rerender(<PublishedResearchWorkspace runId="run_bad" />);
    await waitFor(() => {
      expect(
        screen.getByText("This published research identity is unavailable.")
      ).toBeInTheDocument();
    });
    expect(screen.queryByTestId("published-workspace-retry")).not.toBeInTheDocument();
  });

  it("retries gate failures then loads reference lists after success", async () => {
    const user = userEvent.setup();
    getPublishedRunDetail
      .mockRejectedValueOnce(
        new IntelligenceApiError({
          category: "backend_unavailable",
          transportCode: "HTTP_503",
          status: 503,
        })
      )
      .mockResolvedValue(detail());
    listPublishedRunArtifacts.mockResolvedValue({ run_id: RUN_ID, items: [], count: 0 });
    listPublishedRunSnapshots.mockResolvedValue({ run_id: RUN_ID, items: [], count: 0 });

    render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("published-workspace-retry")).toBeInTheDocument();
    });
    await user.click(screen.getByTestId("published-workspace-retry"));
    await waitFor(() => {
      expect(screen.getByTestId("published-workspace-header")).toBeInTheDocument();
    });
    expect(getPublishedRunDetail).toHaveBeenCalledTimes(2);
    expect(listPublishedRunArtifacts).toHaveBeenCalled();
    expect(listPublishedRunSnapshots).toHaveBeenCalled();
  });

  it("loads Overview summary lazily by snapshot_id without verify and enriches header", async () => {
    mockHappyPath();
    render(<PublishedResearchWorkspace runId={RUN_ID} />);

    await waitFor(() => {
      expect(screen.getByText("Factor Study")).toBeInTheDocument();
    });

    expect(screen.getByTestId("workspace-back-library")).toHaveAttribute("href", "/");
    expect(screen.getByText("PUBLISHED")).toBeInTheDocument();
    expect(screen.getByText("abc1234")).toBeInTheDocument();
    expect(screen.getByTestId("header-analysis-window")).toHaveTextContent("2020-2024");
    expect(getPublishedSnapshotContent).toHaveBeenCalledWith(RUN_ID, "snap_summary");
    expect(getPublishedSnapshotContent.mock.calls[0]).toHaveLength(2);
    expect(getPublishedSnapshotContent).not.toHaveBeenCalledWith(RUN_ID, "snap_signal");
    expect(screen.getByText("Factor remains stable")).toBeInTheDocument();
    expect(screen.getByText("F1 · stability")).toBeInTheDocument();
    expect(screen.getByText("Short sample window")).toBeInTheDocument();
    expect(screen.queryByText(/severity|Buy|Sell/i)).not.toBeInTheDocument();
    expect(within(screen.getByTestId("artifact-summary")).getByText("art_1")).toBeInTheDocument();
    expect(screen.getByText("summary_builder_v1")).toBeInTheDocument();
  });

  it("falls back invalid view to Overview and still loads summary", async () => {
    searchParams = new URLSearchParams("view=nope");
    mockHappyPath();
    render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("overview-view")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText("Factor Study")).toBeInTheDocument();
    });
  });

  it("loads Signals lazily with sort, null placeholders, filter, and full-payload counts", async () => {
    const user = userEvent.setup();
    searchParams = new URLSearchParams("view=signals");
    mockHappyPath();
    render(<PublishedResearchWorkspace runId={RUN_ID} />);

    await waitFor(() => {
      expect(getPublishedSnapshotContent).toHaveBeenCalledWith(RUN_ID, "snap_signal");
    });
    expect(getPublishedSnapshotContent).not.toHaveBeenCalledWith(RUN_ID, "snap_summary");

    const table = screen.getByRole("table", { name: /Published signal records/i });
    const rows = within(table).getAllByRole("row").slice(1);
    expect(within(rows[0]).getByText("AAPL")).toBeInTheDocument();
    expect(within(rows[1]).getByText("MSFT")).toBeInTheDocument();
    expect(screen.getAllByText("Strong negative").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Positive").length).toBeGreaterThan(0);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.queryByText("do-not-render")).not.toBeInTheDocument();
    expect(screen.queryByText(/Buy|Sell|Submit|Broker/i)).not.toBeInTheDocument();

    const strip = screen.getByTestId("signal-direction-strip");
    expect(within(strip).getByText("Strong negative").closest("div")).toHaveTextContent(
      /Strong negative\s*1/
    );
    expect(within(strip).getByText("Positive").closest("div")).toHaveTextContent(
      /Positive\s*1/
    );

    await user.selectOptions(screen.getByTestId("signal-direction-filter"), "positive");
    expect(within(table).queryByText("AAPL")).not.toBeInTheDocument();
    expect(within(table).getByText("MSFT")).toBeInTheDocument();
    expect(within(strip).getByText("Strong negative").closest("div")).toHaveTextContent(
      /Strong negative\s*1/
    );
  });

  it("does not fetch content on Evidence or Validation", async () => {
    searchParams = new URLSearchParams("view=evidence");
    mockHappyPath();
    const { rerender } = render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("evidence-view")).toBeInTheDocument();
    });
    expect(getPublishedSnapshotContent).not.toHaveBeenCalled();

    searchParams = new URLSearchParams("view=validation");
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("validation-view")).toBeInTheDocument();
    });
    expect(getPublishedSnapshotContent).not.toHaveBeenCalled();
    expect(screen.queryByTestId("validation-discrepancy")).not.toBeInTheDocument();
  });

  it("distinguishes missing signal snapshot from empty signal payload", async () => {
    searchParams = new URLSearchParams("view=signals");
    getPublishedRunDetail.mockResolvedValue(detail());
    listPublishedRunArtifacts.mockResolvedValue({ run_id: RUN_ID, items: [], count: 0 });
    listPublishedRunSnapshots.mockResolvedValue({
      run_id: RUN_ID,
      items: [
        snapshot({ snapshot_id: "snap_summary", snapshot_type: "research_summary" }),
      ],
      count: 1,
    });

    const { rerender } = render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(
        screen.getByText("No signal snapshot was published for this run.")
      ).toBeInTheDocument();
    });
    expect(getPublishedSnapshotContent).not.toHaveBeenCalled();

    const signalRef = snapshot({ snapshot_id: "snap_signal", snapshot_type: "signal" });
    getPublishedRunDetail.mockResolvedValue(detail({ run_id: `${RUN_ID}_empty` }));
    listPublishedRunSnapshots.mockResolvedValue({
      run_id: `${RUN_ID}_empty`,
      items: [signalRef],
      count: 1,
    });
    getPublishedSnapshotContent.mockResolvedValue(
      contentDto(signalRef, signalContent({ signals: [] }))
    );
    searchParams = new URLSearchParams("view=signals");
    rerender(<PublishedResearchWorkspace runId={`${RUN_ID}_empty`} />);
    await waitFor(() => {
      expect(
        screen.getByText("This signal snapshot contains no signal records.")
      ).toBeInTheDocument();
    });
  });

  it("renders Evidence references without paths, downloads, or Verified claims", async () => {
    searchParams = new URLSearchParams("view=evidence");
    mockHappyPath();
    render(<PublishedResearchWorkspace runId={RUN_ID} />);

    await waitFor(() => {
      expect(screen.getAllByTestId("snapshot-reference-row").length).toBeGreaterThan(0);
    });

    const evidence = screen.getByTestId("evidence-view");
    const snapshotsSection = screen.getByTestId("evidence-snapshots");
    const artifactsSection = screen.getByTestId("evidence-artifacts");
    expect(evidence.contains(snapshotsSection)).toBe(true);
    expect(evidence.contains(artifactsSection)).toBe(true);
    expect(
      snapshotsSection.compareDocumentPosition(artifactsSection) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();

    expect(within(snapshotsSection).getByText("Consumer contract")).toBeInTheDocument();
    expect(within(artifactsSection).getByText("Opaque evidence")).toBeInTheDocument();
    expect(within(snapshotsSection).getAllByText("Integrity recorded").length).toBeGreaterThan(0);
    expect(screen.queryByText(/^Verified$/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /download/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/\/tmp\//i)).not.toBeInTheDocument();
    expect(getPublishedSnapshotContent).not.toHaveBeenCalled();
  });

  it("keeps Validation usable when artifact list fails and omits summary discrepancy until Overview loads", async () => {
    searchParams = new URLSearchParams("view=validation");
    mockHappyPath({ artifactsFail: true });
    render(<PublishedResearchWorkspace runId={RUN_ID} />);

    await waitFor(() => {
      expect(screen.getByTestId("validation-view")).toBeInTheDocument();
    });
    expect(screen.getByTestId("validation-overall")).toHaveTextContent(/Passed/i);
    expect(screen.getByText("schema_ok")).toBeInTheDocument();
    expect(screen.getByText("No validation errors recorded.")).toBeInTheDocument();
    expect(within(screen.getByTestId("validation-repro")).getByText("ds_v1")).toBeInTheDocument();
    expect(screen.queryByTestId("validation-discrepancy")).not.toBeInTheDocument();
    expect(getPublishedSnapshotContent).not.toHaveBeenCalled();
  });

  it("caches Overview content across revisits and surfaces Validation discrepancy after Overview", async () => {
    mockHappyPath({
      summary: summaryContent({ validation_status: "failed" }),
    });

    const { rerender } = render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("overview-validation-discrepancy")).toBeInTheDocument();
    });
    expect(getPublishedSnapshotContent).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("header-analysis-window")).toHaveTextContent("2020-2024");

    searchParams = new URLSearchParams("view=evidence");
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("evidence-view")).toBeInTheDocument();
    });
    expect(getPublishedSnapshotContent).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("header-analysis-window")).toHaveTextContent("2020-2024");

    searchParams = new URLSearchParams();
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByText("Factor Study")).toBeInTheDocument();
    });
    expect(
      getPublishedSnapshotContent.mock.calls.filter((call) => call[1] === "snap_summary")
    ).toHaveLength(1);

    searchParams = new URLSearchParams("view=validation");
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("validation-discrepancy")).toBeInTheDocument();
    });
    expect(screen.getByTestId("validation-overall")).toHaveTextContent(/Passed/i);
  });

  it("retries only the failed Signals snapshot without clearing Overview cache", async () => {
    const user = userEvent.setup();
    mockHappyPath();
    const { rerender } = render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByText("Factor Study")).toBeInTheDocument();
    });
    const summaryCalls = getPublishedSnapshotContent.mock.calls.filter(
      (call) => call[1] === "snap_summary"
    ).length;

    searchParams = new URLSearchParams("view=signals");
    getPublishedSnapshotContent.mockImplementationOnce(async () => {
      throw new IntelligenceApiError({
        category: "backend_unavailable",
        transportCode: "HTTP_503",
        status: 503,
      });
    });
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
    });

    getPublishedSnapshotContent.mockImplementation(
      async (_runId: string, snapshotId: string) => {
        if (snapshotId === "snap_signal") {
          return contentDto(
            snapshot({ snapshot_id: "snap_signal", snapshot_type: "signal" }),
            signalContent()
          );
        }
        return contentDto(
          snapshot({ snapshot_id: "snap_summary", snapshot_type: "research_summary" }),
          summaryContent()
        );
      }
    );
    await user.click(screen.getByRole("button", { name: /Retry/i }));
    await waitFor(() => {
      expect(screen.getByRole("table", { name: /Published signal records/i })).toBeInTheDocument();
    });

    searchParams = new URLSearchParams();
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByText("Factor Study")).toBeInTheDocument();
    });
    expect(
      getPublishedSnapshotContent.mock.calls.filter((call) => call[1] === "snap_summary")
    ).toHaveLength(summaryCalls);
  });

  it("keeps Evidence available when summary content is invalid and never dumps raw JSON", async () => {
    mockHappyPath();
    getPublishedSnapshotContent.mockImplementation(async (_runId, snapshotId) => {
      if (snapshotId === "snap_summary") {
        return {
          run_id: RUN_ID,
          reference: snapshot({
            snapshot_id: "snap_summary",
            snapshot_type: "research_summary",
          }),
          content: { not: "a summary", rawDump: '{"evil":true}' },
        };
      }
      return contentDto(
        snapshot({ snapshot_id: "snap_signal", snapshot_type: "signal" }),
        signalContent()
      );
    });

    const { rerender } = render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(
        screen.getByText("Research summary snapshot content is invalid.")
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/rawDump|evil/i)).not.toBeInTheDocument();

    searchParams = new URLSearchParams("view=evidence");
    rerender(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("evidence-view")).toBeInTheDocument();
    });
    expect(screen.getAllByTestId("snapshot-reference-row").length).toBeGreaterThan(0);
  });

  it("enriches universe from summary only when run.universe is null", async () => {
    mockHappyPath({
      run: { universe: null },
      summary: summaryContent({ universe: "summary-universe" }),
    });
    render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByText("Factor Study")).toBeInTheDocument();
    });
    expect(screen.getByTestId("published-workspace-header")).toHaveTextContent(
      "summary-universe"
    );
  });

  it("exposes accessible navigation and headings", async () => {
    mockHappyPath();
    render(<PublishedResearchWorkspace runId={RUN_ID} />);
    await waitFor(() => {
      expect(screen.getByTestId("published-workspace-nav")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("navigation", { name: /Published workspace views/i })
    ).toBeInTheDocument();
    expect(screen.getByTestId("workspace-back-library")).toHaveAccessibleName(
      /Back to Research Library/i
    );
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Overview" })).toBeInTheDocument();
    });
  });
});
