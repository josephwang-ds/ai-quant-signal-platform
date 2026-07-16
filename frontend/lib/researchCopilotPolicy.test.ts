import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const FRONTEND_ROOT = join(__dirname, "..");

function walk(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".next") {
        return [];
      }
      return walk(path);
    }
    return [path];
  });
}

describe("research copilot repository policy", () => {
  it("does not expose provider API keys via NEXT_PUBLIC variables", () => {
    const envExample = readFileSync(join(FRONTEND_ROOT, ".env.example"), "utf8");
    expect(envExample).not.toMatch(/NEXT_PUBLIC_.*API_KEY/i);
  });

  it("does not import OpenAI, Anthropic, or DeepSeek SDKs in frontend source", () => {
    const sourceFiles = walk(FRONTEND_ROOT).filter((file) =>
      /\.(ts|tsx)$/.test(file)
    );
    const combined = sourceFiles
      .map((file) => readFileSync(file, "utf8"))
      .join("\n");
    expect(combined).not.toMatch(/from ["']openai["']/);
    expect(combined).not.toMatch(/from ["']@anthropic-ai\/sdk["']/);
    expect(combined).not.toMatch(/api\.openai\.com/);
    expect(combined).not.toMatch(/api\.deepseek\.com/);
    expect(combined).not.toMatch(/NEXT_PUBLIC_(OPENAI|LLM|DEEPSEEK)_API_KEY/);
  });

  it("does not ship a mock copilot answer presented as generated output", () => {
    const panelSource = readFileSync(
      join(
        FRONTEND_ROOT,
        "components/features/research/copilot/ResearchCopilotPanel.tsx"
      ),
      "utf8"
    );
    expect(panelSource).not.toMatch(/MOCK_COPILOT_ANSWER/);
    expect(panelSource).not.toMatch(/fake generated answer/i);
  });
});
