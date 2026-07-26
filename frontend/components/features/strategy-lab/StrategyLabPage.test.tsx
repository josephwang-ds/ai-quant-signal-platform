import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import StrategyLabPage from "@/components/features/strategy-lab/StrategyLabPage";
import { translations } from "@/lib/i18n";

const getDatabaseStatus = vi.fn();
const runBacktest = vi.fn();
const saveBacktestRun = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/strategy-lab",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("next/dynamic", () => ({
  default: () => {
    function Stub() {
      return null;
    }
    return Stub;
  },
}));

vi.mock("@/lib/useWorkspaceLanguage", () => ({
  useWorkspaceLanguage: () => ({
    language: "en" as const,
    setLanguage: vi.fn(),
    tr: (key: keyof typeof translations.en) => translations.en[key],
  }),
}));

vi.mock("@/lib/api", () => ({
  getDatabaseStatus: (...args: unknown[]) => getDatabaseStatus(...args),
  runBacktest: (...args: unknown[]) => runBacktest(...args),
  saveBacktestRun: (...args: unknown[]) => saveBacktestRun(...args),
}));

describe("StrategyLabPage archive capability", () => {
  beforeEach(() => {
    getDatabaseStatus.mockReset();
    runBacktest.mockReset();
    saveBacktestRun.mockReset();
  });

  it("keeps Run Backtest enabled and disables Save Run when DB is not configured", async () => {
    getDatabaseStatus.mockResolvedValue({
      configured: false,
      connected: false,
      message: "Database is not configured.",
      database: "supabase_postgres",
    });

    render(<StrategyLabPage />);

    await waitFor(() => {
      expect(screen.getByTestId("strategy-lab-archive-status")).toHaveTextContent(
        translations.en.strategyLabArchiveOptional
      );
    });

    expect(screen.getByTestId("strategy-lab-run-backtest")).not.toBeDisabled();
    expect(screen.getByTestId("strategy-lab-save-run")).toBeDisabled();
    expect(document.body.textContent).not.toMatch(/SUPABASE_DB_URL/);
    expect(document.body.textContent).not.toMatch(/traceback/i);
  });

  it("enables Save Run only after a result when archive storage is available", async () => {
    getDatabaseStatus.mockResolvedValue({
      configured: true,
      connected: true,
      message: "Database connection successful.",
      database: "supabase_postgres",
    });

    render(<StrategyLabPage />);

    await waitFor(() => {
      expect(screen.getByTestId("strategy-lab-archive-panel")).toHaveAttribute(
        "data-archive-availability",
        "available"
      );
    });

    // No result yet — still disabled
    expect(screen.getByTestId("strategy-lab-save-run")).toBeDisabled();
    expect(screen.getByTestId("strategy-lab-run-backtest")).not.toBeDisabled();
  });

  it("shows a safe unavailable notice without leaking internals", async () => {
    getDatabaseStatus.mockResolvedValue({
      configured: true,
      connected: false,
      message: "Database connection failed.",
      database: "supabase_postgres",
    });

    render(<StrategyLabPage />);

    await waitFor(() => {
      expect(screen.getByTestId("strategy-lab-archive-status")).toHaveTextContent(
        translations.en.strategyLabArchiveUnavailable
      );
    });

    expect(screen.getByTestId("strategy-lab-save-run")).toBeDisabled();
    expect(screen.getByTestId("strategy-lab-archive-retry")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/SUPABASE_DB_URL/);
    expect(document.body.textContent).not.toMatch(/psycopg|connection string/i);
  });
});
