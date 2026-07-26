import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ReproducibilityManifestPanel from "@/components/features/research/ReproducibilityManifestPanel";
import type { ReproducibilityManifest } from "@/types/reproducibility";

const SAMPLE: ReproducibilityManifest = {
  data_source: "fixture",
  symbol: "SPY",
  universe: "__MISSING__",
  requested_start_date: "2018-01-01",
  requested_end_date: "2021-01-01",
  actual_start_date: "2018-01-02",
  actual_end_date: "2020-12-31",
  retrieval_timestamp: "2026-07-26T00:00:00Z",
  row_count: 100,
  adjustment_mode: "auto",
  protocol_version: "reproducibility-manifest/v1",
  protocol_hash: "abcdef0123456789ffffffffffffffffffffffffffffffffffffffffffff",
  data_hash: "1234567890abcdefffffffffffffffffffffffffffffffffffffffffffff",
  engine_version: "research-calc/v1",
  git_commit_sha: "unavailable",
  runtime_version: "python/3.12.0",
  created_at: "2026-07-26T00:00:00Z",
};

describe("ReproducibilityManifestPanel", () => {
  it("shows short provenance and truncated hashes by default", () => {
    render(<ReproducibilityManifestPanel manifest={SAMPLE} language="en" />);
    expect(screen.getByText("Reproducibility")).toBeInTheDocument();
    expect(screen.getAllByText("fixture").length).toBeGreaterThan(0);
    expect(screen.getAllByText("abcdef0123").length).toBeGreaterThan(0);
    expect(screen.getAllByText("1234567890").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/not a certification or security guarantee/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Full manifest")).toBeInTheDocument();
  });

  it("renders nothing without a manifest", () => {
    const { container } = render(
      <ReproducibilityManifestPanel manifest={null} language="en" />
    );
    expect(container).toBeEmptyDOMElement();
  });
});
