import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import FeatureInterpretationPage from "@/components/features/comparison/FeatureInterpretationPage";
import { translations } from "@/lib/i18n";

vi.mock("@/lib/useWorkspaceLanguage", () => ({
  useWorkspaceLanguage: () => ({
    language: "en" as const,
    setLanguage: vi.fn(),
    tr: (key: keyof typeof translations.en) => translations.en[key],
  }),
}));

vi.mock("@/lib/api", () => ({
  runModelComparison: vi.fn(),
}));

describe("FeatureInterpretationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a single level-1 heading from i18n", () => {
    render(<FeatureInterpretationPage />);

    const headings = screen.getAllByRole("heading", { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent(translations.en.featureInterpTitle);
    expect(
      screen.getByText(translations.en.featureInterpCausality)
    ).toBeInTheDocument();
  });

  it("renders the Chinese h1 from i18n when language is zh", async () => {
    vi.resetModules();
    vi.doMock("@/lib/useWorkspaceLanguage", () => ({
      useWorkspaceLanguage: () => ({
        language: "zh" as const,
        setLanguage: vi.fn(),
        tr: (key: keyof typeof translations.zh) => translations.zh[key],
      }),
    }));
    const { default: PageZh } = await import(
      "@/components/features/comparison/FeatureInterpretationPage"
    );
    render(<PageZh />);
    const headings = screen.getAllByRole("heading", { level: 1 });
    expect(headings).toHaveLength(1);
    expect(headings[0]).toHaveTextContent(translations.zh.featureInterpTitle);
  });
});
