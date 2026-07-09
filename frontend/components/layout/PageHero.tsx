"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <header className={`dashboard-header${isHome ? "" : " dashboard-header--compact"}`}>
      <div className="dashboard-header__inner">
        <LanguageToggle language={language} onLanguageChange={onLanguageChange} />
        {isHome ? (
          <h1 className="dashboard-title">{t(language, "appTitle")}</h1>
        ) : (
          <Link href="/" className="dashboard-title dashboard-title--link">
            {t(language, "appTitleShort")}
          </Link>
        )}
        {isHome ? (
          <>
            <p className="dashboard-subtitle">{t(language, "appSubtitle")}</p>
            <div className="dashboard-badges">
              <StatusBadge label={t(language, "educationalDemo")} variant="info" />
              <StatusBadge label={t(language, "notFinancialAdvice")} variant="warning" />
            </div>
          </>
        ) : null}
        <TopNav language={language} />
      </div>
    </header>
  );
}
