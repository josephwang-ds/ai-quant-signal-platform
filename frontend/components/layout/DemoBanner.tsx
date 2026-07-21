"use client";

import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";

type DemoBannerProps = {
  language: Language;
};

/**
 * Subtle portfolio-demo notice — always visible, never a modal.
 */
export default function DemoBanner({ language }: DemoBannerProps) {
  return (
    <aside className="demo-banner" role="note" aria-label={t(language, "demoBannerLabel")}>
      <span className="demo-banner__lead">{t(language, "demoBannerLead")}</span>
      <ul className="demo-banner__list">
        <li>{t(language, "demoBannerResearchOnly")}</li>
        <li>{t(language, "demoBannerNotAdvice")}</li>
        <li>{t(language, "demoBannerNoLiveTrading")}</li>
        <li>{t(language, "demoBannerNoBroker")}</li>
      </ul>
    </aside>
  );
}
