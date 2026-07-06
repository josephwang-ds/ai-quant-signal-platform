"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Language, TranslationKey } from "@/lib/i18n";
import { t } from "@/lib/i18n";

const NAV_ITEMS: Array<{ href: string; labelKey: TranslationKey }> = [
  { href: "/", labelKey: "navOverview" },
  { href: "/data-center", labelKey: "navDataCenter" },
  { href: "/market-watch", labelKey: "navMarketWatch" },
  { href: "/strategy-lab", labelKey: "navStrategyLab" },
  { href: "/comparison", labelKey: "navComparison" },
  { href: "/robustness", labelKey: "navRobustness" },
  { href: "/model-lab", labelKey: "navModelLab" },
  { href: "/experiments", labelKey: "navExperiments" },
  { href: "/research-notes", labelKey: "navResearchNotes" },
  { href: "/ai-agent", labelKey: "navAiAgent" },
];

type TopNavProps = {
  language: Language;
};

export default function TopNav({ language }: TopNavProps) {
  const pathname = usePathname();

  return (
    <nav className="dashboard-nav" aria-label="Workspace modules">
      {NAV_ITEMS.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "is-active" : undefined}
          >
            {t(language, item.labelKey)}
          </Link>
        );
      })}
    </nav>
  );
}
