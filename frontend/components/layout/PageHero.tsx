"use client";

import StatusBadge from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";

type PageHeroProps = {
  language: Language;
};

/** 仅首页展示的简短介绍条 */
export default function PageHero({ language }: PageHeroProps) {
  return (
    <header className="workspace-home-banner">
      <h1 className="workspace-home-banner__title">{t(language, "appTitle")}</h1>
      <p className="workspace-home-banner__subtitle">{t(language, "appSubtitle")}</p>
      <div className="workspace-home-banner__badges">
        <StatusBadge label={t(language, "educationalDemo")} variant="info" />
        <StatusBadge label={t(language, "notFinancialAdvice")} variant="warning" />
      </div>
    </header>
  );
}
