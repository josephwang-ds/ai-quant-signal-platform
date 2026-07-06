"use client";

import type { ReactNode } from "react";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import PageHero from "./PageHero";

type AppShellProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
  children: ReactNode;
};

export default function AppShell({
  language,
  onLanguageChange,
  children,
}: AppShellProps) {
  return (
    <main className="dashboard-page">
      <div className="dashboard-container">
        <PageHero language={language} onLanguageChange={onLanguageChange} />
        {children}
        <footer className="dashboard-footer">
          {t(language, "footerLine1")} {t(language, "footerLine2")}{" "}
          {t(language, "footerLine3")}
        </footer>
      </div>
    </main>
  );
}
