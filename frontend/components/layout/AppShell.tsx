"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import {
  PRODUCT_COPYRIGHT,
  PRODUCT_REPO_URL,
  PRODUCT_VERSION,
} from "@/lib/productIdentity";
import DemoBanner from "./DemoBanner";
import LanguageToggle from "./LanguageToggle";
import PageHero from "./PageHero";
import SideNav from "./SideNav";

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
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <Link href="/" className="workspace-brand">
          {t(language, "appTitleShort")}
        </Link>
        <SideNav language={language} />
        <div className="workspace-sidebar__footer">
          <LanguageToggle language={language} onLanguageChange={onLanguageChange} />
        </div>
      </aside>

      <main className="workspace-main">
        <DemoBanner language={language} />
        {isHome ? <PageHero language={language} /> : null}
        <div className="workspace-content">{children}</div>
        <footer className="workspace-footer">
          <p className="workspace-footer__identity">
            {t(language, "appTitle")} · v{PRODUCT_VERSION}
          </p>
          <p className="workspace-footer__legal">
            {PRODUCT_COPYRIGHT} · {t(language, "footerLicense")}
          </p>
          <p className="workspace-footer__disclaimer">
            {t(language, "footerLine1")} {t(language, "footerLine2")}{" "}
            {t(language, "footerLine3")}
          </p>
          <p className="workspace-footer__repo">
            <a href={PRODUCT_REPO_URL} target="_blank" rel="noreferrer">
              {t(language, "footerRepository")}
            </a>
          </p>
        </footer>
      </main>
    </div>
  );
}
