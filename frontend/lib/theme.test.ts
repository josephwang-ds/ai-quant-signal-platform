import { describe, expect, it } from "vitest";
import {
  applyTheme,
  isThemePreference,
  resolveTheme,
} from "@/lib/theme";

describe("theme", () => {
  it("validates persisted preferences", () => {
    expect(isThemePreference("light")).toBe(true);
    expect(isThemePreference("dark")).toBe(true);
    expect(isThemePreference("system")).toBe(true);
    expect(isThemePreference("midnight")).toBe(false);
    expect(isThemePreference(null)).toBe(false);
  });

  it("resolves system preference deterministically", () => {
    expect(resolveTheme("system", true)).toBe("dark");
    expect(resolveTheme("system", false)).toBe("light");
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
  });

  it("applies resolved theme and preference to the root", () => {
    const root = document.createElement("html");

    expect(applyTheme("system", true, root)).toBe("dark");
    expect(root.dataset.theme).toBe("dark");
    expect(root.dataset.themePreference).toBe("system");
    expect(root.style.colorScheme).toBe("dark");
  });
});
