"use client";

import Link from "next/link";

/**
 * Compact operating-overview hero for the workspace homepage.
 * Stats and CTA are supplied by the page — never invents metrics.
 */

type Stat = {
  label: string;
  value: string | number;
};

type PrimaryCta =
  | { label: string; href: string; onClick?: undefined }
  | { label: string; href?: undefined; onClick: () => void };

type PageHeroProps = {
  title: string;
  sentence: string;
  stats: Stat[];
  primaryCta: PrimaryCta;
};

export default function PageHero({ title, sentence, stats, primaryCta }: PageHeroProps) {
  return (
    <header className="workspace-home-hero" data-testid="workspace-home-hero">
      <div className="workspace-home-hero__copy">
        <h1 className="workspace-home-hero__title">{title}</h1>
        <p className="workspace-home-hero__sentence">{sentence}</p>
      </div>

      {stats.length > 0 ? (
        <dl className="workspace-home-hero__stats" aria-label="Workspace statistics">
          {stats.map((stat) => (
            <div key={stat.label} className="workspace-home-hero__stat">
              <dt>{stat.label}</dt>
              <dd>{stat.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      <div className="workspace-home-hero__cta">
        {"href" in primaryCta && primaryCta.href ? (
          <Link href={primaryCta.href} className="btn btn--primary">
            {primaryCta.label}
          </Link>
        ) : (
          <button type="button" className="btn btn--primary" onClick={primaryCta.onClick}>
            {primaryCta.label}
          </button>
        )}
      </div>
    </header>
  );
}
