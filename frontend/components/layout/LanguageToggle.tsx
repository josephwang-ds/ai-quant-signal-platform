"use client";

import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";

type LanguageToggleProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
};

export default function LanguageToggle({
  language,
  onLanguageChange,
}: LanguageToggleProps) {
  return (
    <div className="language-toggle">
      <button
        type="button"
        className={`language-toggle__btn${language === "en" ? " is-active" : ""}`}
        onClick={() => onLanguageChange("en")}
      >
        {t(language, "langEnglish")}
      </button>
      <button
        type="button"
        className={`language-toggle__btn${language === "zh" ? " is-active" : ""}`}
        onClick={() => onLanguageChange("zh")}
      >
        {t(language, "langChinese")}
      </button>
    </div>
  );
}
