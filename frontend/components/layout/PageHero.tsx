"use client";

import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import LanguageToggle from "./LanguageToggle";
import TopNav from "./TopNav";

type PageHeroProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
};

export default function PageHero({ language, onLanguageChange }: PageHeroProps) {
  return (
    <header className="dashboard-header">
      <div className="dashboard-header__inner">
        <LanguageToggle language={language} onLanguageChange={onLanguageChange} />
        <h1 className="dashboard-title">{t(language, "appTitle")}</h1>
        <p className="dashboard-subtitle">{t(language, "appSubtitle")}</p>
        <div className="dashboard-badges">
          <StatusBadge label={t(language, "educationalDemo")} variant="info" />
          <StatusBadge label={t(language, "dailyMarketData")} variant="neutral" />
          <StatusBadge label={t(language, "notFinancialAdvice")} variant="warning" />
        </div>
        <TopNav language={language} />
      </div>
    </header>
  );
}
