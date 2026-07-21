"use client";

import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";

type PageHeroProps = {
  language: Language;
};

/**
 * Home-only product framing — what / who / problem / how to start.
 * Copy only; no marketing flourish.
 */
export default function PageHero({ language }: PageHeroProps) {
  return (
    <header className="workspace-home-banner">
      <p className="workspace-home-banner__eyebrow">{t(language, "landingEyebrow")}</p>
      <h1 className="workspace-home-banner__title">{t(language, "appTitle")}</h1>
      <p className="workspace-home-banner__subtitle">{t(language, "landingWhat")}</p>
      <dl className="workspace-home-banner__facts">
        <div>
          <dt>{t(language, "landingWhoLabel")}</dt>
          <dd>{t(language, "landingWho")}</dd>
        </div>
        <div>
          <dt>{t(language, "landingProblemLabel")}</dt>
          <dd>{t(language, "landingProblem")}</dd>
        </div>
        <div>
          <dt>{t(language, "landingStartLabel")}</dt>
          <dd>{t(language, "landingStart")}</dd>
        </div>
      </dl>
    </header>
  );
}
