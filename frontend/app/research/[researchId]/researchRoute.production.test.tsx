import { readFileSync } from "node:fs";
import path from "node:path";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import ResearchDetailError from "@/app/research/[researchId]/error";
import { getMockResearchById } from "@/lib/mockResearchCatalog";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { getApiBaseUrl, ApiConfigurationError } from "@/lib/apiConfig";

const ROUTE_DIR = path.join(
  process.cwd(),
  "app/research/[researchId]"
);

function readRoute(fileName: string): string {
  return readFileSync(path.join(ROUTE_DIR, fileName), "utf8");
}

describe("PR-017 research route production safety", () => {
  it("awaits Promise params and does not pass Server→Client event handlers", () => {
    const source = readRoute("page.tsx");
    expect(source).toMatch(/params:\s*Promise<\{\s*researchId:\s*string\s*\}>/);
    expect(source).toMatch(/await params/);
    expect(source).not.toMatch(/onLanguageChange=/);
    expect(source).not.toMatch(/from "@\/components\/layout\/AppShell"/);
    expect(source).not.toMatch(/<AppShell[\s>]/);
  });

  it("provides honest loading and error boundaries", () => {
    const loading = readRoute("loading.tsx");
    const error = readRoute("error.tsx");
    expect(loading).toContain("ResearchWorkspaceSkeleton");
    expect(loading).not.toMatch(/42\.0%/);
    expect(loading.toLowerCase()).not.toContain("mock metrics");
    expect(error).toMatch(/^"use client"/m);
    expect(error).toContain("The Research Workspace could not be loaded.");
    expect(error).toContain("reset()");
    // Must not render digests/stacks in UI text; console diagnostics are OK.
    expect(error).not.toMatch(/>\s*\{[^}]*digest/);
    expect(error).not.toMatch(/error\.digest|error\.stack/);
  });

  it("keeps unsupported research IDs controlled (no throw from catalog)", () => {
    expect(getMockResearchById("does-not-exist")).toBeNull();
    expect(getMockResearchById(CANONICAL_RESEARCH_ID)?.id).toBe(
      CANONICAL_RESEARCH_ID
    );
  });

  it("does not resolve API base URL at apiConfig module import", async () => {
    vi.resetModules();
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");
    const mod = await import("@/lib/apiConfig");
    expect(typeof mod.getApiBaseUrl).toBe("function");
    expect(() => mod.getApiBaseUrl()).toThrow(mod.ApiConfigurationError);
    vi.unstubAllEnvs();
  });

  it("refuses localhost fallback messaging when production env is missing", () => {
    vi.stubEnv("NODE_ENV", "production");
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");
    expect(() => getApiBaseUrl()).toThrow(ApiConfigurationError);
    expect(() => getApiBaseUrl()).not.toThrow(/localhost|127\.0\.0\.1/i);
    vi.unstubAllEnvs();
  });

  it("renders the route error boundary without digest or fake metrics", async () => {
    const user = userEvent.setup();
    const reset = vi.fn();
    render(
      <ResearchDetailError
        error={Object.assign(new Error("boom"), { digest: "440809330" })}
        reset={reset}
      />
    );

    expect(
      screen.getByText("The Research Workspace could not be loaded.")
    ).toBeInTheDocument();
    expect(screen.queryByText(/440809330/)).not.toBeInTheDocument();
    expect(screen.queryByText(/digest/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/42\.0%/)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /research list/i })).toHaveAttribute(
      "href",
      "/"
    );

    await user.click(screen.getByRole("button", { name: /retry/i }));
    expect(reset).toHaveBeenCalledTimes(1);
  });
});
