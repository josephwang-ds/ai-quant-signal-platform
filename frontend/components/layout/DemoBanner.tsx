"use client";

import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";

type DemoBannerProps = {
  language: Language;
};

/**
 * Thin portfolio-demo notice — one-line tip, never a modal or large block.
 */
export default function DemoBanner({ language }: DemoBannerProps) {
  const parts = [
    t(language, "demoBannerLead"),
    t(language, "demoBannerResearchOnly"),
    t(language, "demoBannerNotAdvice"),
    t(language, "demoBannerNoLiveTrading"),
    t(language, "demoBannerNoBroker"),
  ];

  return (
    <aside className="demo-banner" role="note" aria-label={t(language, "demoBannerLabel")}>
      <p className="demo-banner__line">
        {parts.map((part, index) => (
          <span key={part}>
            {index > 0 ? <span className="demo-banner__sep" aria-hidden="true"> · </span> : null}
            <span className={index === 0 ? "demo-banner__lead" : undefined}>{part}</span>
          </span>
        ))}
      </p>
    </aside>
  );
}
