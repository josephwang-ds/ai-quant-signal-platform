import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import PlatformHomePage from "@/components/features/platform/PlatformHomePage";
import ResearchEngineHomePage from "@/components/features/platform/ResearchEngineHomePage";
import {
  ENGINE_STAGES,
  FLAGSHIP_RESEARCH,
  getContinueTarget,
} from "@/lib/platformArchitecture";

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

describe("IA V2 platform home", () => {
  it("positions the product as an intelligence platform, not a research library", () => {
    render(<PlatformHomePage />);
    expect(screen.getByTestId("platform-home-hero")).toHaveTextContent(
      "AI Investment Intelligence Platform"
    );
    expect(screen.getByTestId("product-tagline")).toHaveTextContent(
      "Built on an Evidence-driven Quant Research Engine."
    );
    expect(screen.getByTestId("product-philosophy")).toHaveTextContent(
      "Explainable. Traceable. Reviewable."
    );
    expect(screen.getByTestId("intelligence-grid")).toBeInTheDocument();
    expect(screen.getByTestId("research-engine-status")).toBeInTheDocument();
    expect(screen.queryByText("Research library")).not.toBeInTheDocument();
    expect(screen.queryByText("Continue research")).not.toBeInTheDocument();
    expect(screen.queryByText("Recent activity")).not.toBeInTheDocument();
  });

  it("exposes all six intelligence modules without inventing rankings", () => {
    render(<PlatformHomePage />);
    for (const id of [
      "market",
      "research",
      "signal",
      "portfolio",
      "risk",
      "assistant",
    ]) {
      expect(screen.getByTestId(`intelligence-card-${id}`)).toBeInTheDocument();
    }
    expect(screen.getByTestId("intelligence-card-signal")).toHaveTextContent(
      "withheld until Portfolio Construction"
    );
  });

  it("surfaces engine progress with Portfolio Construction as current", () => {
    render(<PlatformHomePage />);
    expect(screen.getByTestId("engine-current-stage")).toHaveTextContent(
      "Portfolio Construction"
    );
    expect(screen.getByTestId("engine-progress")).toHaveTextContent("5/8");
    expect(screen.getByTestId("continue-engine-stage")).toHaveAttribute(
      "href",
      "/engine/portfolio"
    );
  });
});

describe("Quant Research Engine home", () => {
  it("renders eight ordered stages with Feature Engineering included", () => {
    render(<ResearchEngineHomePage />);
    expect(ENGINE_STAGES).toHaveLength(8);
    expect(screen.getByTestId("workflow-step-features")).toHaveAttribute(
      "data-status",
      "completed"
    );
    expect(screen.getByTestId("workflow-step-portfolio")).toHaveAttribute(
      "data-status",
      "current"
    );
    expect(screen.getByTestId("workflow-step-backtest")).toHaveAttribute(
      "data-status",
      "locked"
    );
    expect(getContinueTarget().id).toBe("portfolio");
    expect(screen.getByTestId("research-flow-hero")).toHaveTextContent(
      FLAGSHIP_RESEARCH.nameEn
    );
  });

  it("keeps Trend Following as a legacy demo only", () => {
    render(<ResearchEngineHomePage />);
    const legacy = screen.getByTestId("legacy-trend-demo");
    expect(legacy).toHaveTextContent("Legacy demonstration");
    expect(within(legacy).getByTestId("open-trend-demo")).toBeInTheDocument();
  });

  it("discloses the static US Liquid 31 universe", () => {
    render(<ResearchEngineHomePage />);
    expect(screen.getByTestId("universe-details")).toHaveTextContent(
      "Static demo universe"
    );
  });
});
