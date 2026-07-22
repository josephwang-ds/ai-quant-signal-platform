import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import NewsSentimentPanel from "@/components/features/insights/NewsSentimentPanel";

const runNewsSentiment = vi.fn();

vi.mock("@/lib/api", () => ({
  runNewsSentiment: (...args: unknown[]) => runNewsSentiment(...args),
}));

vi.mock("@/lib/useWorkspaceLanguage", () => ({
  useWorkspaceLanguage: () => ({
    language: "en" as const,
    setLanguage: vi.fn(),
    tr: (key: string) => key,
  }),
}));

describe("NewsSentimentPanel", () => {
  beforeEach(() => {
    runNewsSentiment.mockReset();
  });

  it("renders overall score, counts, and item stance after analyze", async () => {
    const user = userEvent.setup();
    runNewsSentiment.mockResolvedValue({
      ticker: "SPY",
      overall: {
        stance: "favourable",
        score_1_5: 4,
        counts: { positive: 2, neutral: 1, negative: 0 },
      },
      items: [
        {
          headline: "Earnings beat",
          url: "https://example.test/a",
          source: "Wire",
          published_at: "2026-07-20T12:00:00+00:00",
          stance: "favourable",
          score_1_5: 5,
          reason: "Lexicon polarity=+1.00",
          llm_stance: "favourable",
          llm_score_1_5: 5,
        },
      ],
      summary: {
        text: "Tone is constructive on the supplied headlines.",
        disclaimer: "AI interpretation — not investment advice.",
      },
      agreement: {
        n_compared: 3,
        n_agree_stance: 2,
        n_agree_score: 2,
        stance_agreement: 0.6667,
        score_agreement: 0.6667,
        note: "Classifier remains authoritative.",
      },
      provider: "fixture",
      classifier: "loughran_mcdonald_lite",
      notice: "Live snapshot; not a backtest feature.",
      backtest_feature: false,
    });

    render(<NewsSentimentPanel defaultTicker="SPY" />);
    await user.click(screen.getByTestId("news-sentiment-run"));

    expect(runNewsSentiment).toHaveBeenCalledWith(
      expect.objectContaining({
        ticker: "SPY",
        use_finbert: false,
        fetch_latest: true,
      })
    );
    expect(screen.getByTestId("news-sentiment-overall")).toHaveTextContent("4/5");
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Earnings beat")).toBeInTheDocument();
    expect(
      screen.getByText("Tone is constructive on the supplied headlines.")
    ).toBeInTheDocument();
    expect(screen.getByTestId("news-sentiment-agreement")).toBeInTheDocument();
    expect(screen.getByTestId("news-sentiment-agreement-stance")).toHaveTextContent(
      "66.7%"
    );
    expect(screen.getByTestId("news-sentiment-agreement-score")).toHaveTextContent(
      "66.7%"
    );
    expect(screen.getByText(/newsSentimentLlmShadow/)).toBeInTheDocument();
  });

  it("passes use_finbert when the optional switch is checked", async () => {
    const user = userEvent.setup();
    runNewsSentiment.mockResolvedValue({
      ticker: "AAPL",
      overall: { stance: "neutral", score_1_5: 3, counts: { positive: 0, neutral: 0, negative: 0 } },
      items: [],
      summary: null,
      notice: "Live snapshot",
    });

    render(<NewsSentimentPanel defaultTicker="AAPL" />);
    await user.click(screen.getByTestId("news-sentiment-finbert"));
    await user.click(screen.getByTestId("news-sentiment-run"));

    expect(runNewsSentiment).toHaveBeenCalledWith(
      expect.objectContaining({ ticker: "AAPL", use_finbert: true })
    );
  });
});
