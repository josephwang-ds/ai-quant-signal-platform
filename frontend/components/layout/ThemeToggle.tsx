"use client";

import { useEffect, useState } from "react";
import type { Language } from "@/lib/i18n";
import {
  applyTheme,
  isThemePreference,
  THEME_PREFERENCES,
  THEME_STORAGE_KEY,
  type ThemePreference,
} from "@/lib/theme";

type ThemeToggleProps = {
  language: Language;
  compact?: boolean;
};

const LABELS = {
  en: {
    group: "Appearance",
    light: "Light",
    dark: "Dark",
    system: "System",
  },
  zh: {
    group: "外观主题",
    light: "浅色",
    dark: "深色",
    system: "跟随系统",
  },
} satisfies Record<Language, Record<"group" | ThemePreference, string>>;

const ICONS: Record<ThemePreference, string> = {
  light: "☀",
  dark: "☾",
  system: "◐",
};

function readStoredPreference(): ThemePreference {
  try {
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
    return isThemePreference(stored) ? stored : "system";
  } catch {
    return "system";
  }
}

export default function ThemeToggle({
  language,
  compact = false,
}: ThemeToggleProps) {
  const [preference, setPreference] = useState<ThemePreference>("system");

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const storedPreference = readStoredPreference();

    setPreference(storedPreference);
    applyTheme(storedPreference, media.matches);

    const syncSystemTheme = (event: MediaQueryListEvent) => {
      if (readStoredPreference() === "system") {
        applyTheme("system", event.matches);
      }
    };

    media.addEventListener("change", syncSystemTheme);
    return () => media.removeEventListener("change", syncSystemTheme);
  }, []);

  const selectTheme = (nextPreference: ThemePreference) => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    setPreference(nextPreference);
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, nextPreference);
    } catch {
      // Theme still applies for this session when storage is unavailable.
    }
    applyTheme(nextPreference, media.matches);
  };

  return (
    <div
      className={`theme-toggle${compact ? " theme-toggle--compact" : ""}`}
      role="group"
      aria-label={LABELS[language].group}
    >
      {THEME_PREFERENCES.map((option) => (
        <button
          key={option}
          type="button"
          className={`theme-toggle__btn${
            preference === option ? " is-active" : ""
          }`}
          aria-label={LABELS[language][option]}
          aria-pressed={preference === option}
          title={LABELS[language][option]}
          onClick={() => selectTheme(option)}
        >
          <span aria-hidden="true">{ICONS[option]}</span>
          {compact ? null : (
            <span className="theme-toggle__label">
              {LABELS[language][option]}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
