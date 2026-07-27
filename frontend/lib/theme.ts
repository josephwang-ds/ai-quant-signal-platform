export const THEME_STORAGE_KEY = "ai-quant-theme";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export const THEME_PREFERENCES: readonly ThemePreference[] = [
  "light",
  "dark",
  "system",
];

export function isThemePreference(value: unknown): value is ThemePreference {
  return (
    typeof value === "string" &&
    THEME_PREFERENCES.includes(value as ThemePreference)
  );
}

export function resolveTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean
): ResolvedTheme {
  if (preference === "system") {
    return systemPrefersDark ? "dark" : "light";
  }
  return preference;
}

export function applyTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean,
  root: HTMLElement = document.documentElement
): ResolvedTheme {
  const resolved = resolveTheme(preference, systemPrefersDark);
  root.dataset.theme = resolved;
  root.dataset.themePreference = preference;
  root.style.colorScheme = resolved;
  return resolved;
}
