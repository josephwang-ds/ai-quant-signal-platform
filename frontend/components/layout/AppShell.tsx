"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import QuantTip from "@/components/ui/QuantTip";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
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
        <QuantTip language={language} />
        <div className="workspace-sidebar__footer">
          <LanguageToggle language={language} onLanguageChange={onLanguageChange} />
        </div>
      </aside>

      <main className="workspace-main">
        {isHome ? <PageHero language={language} /> : null}
        <div className="workspace-content">{children}</div>
        <footer className="dashboard-footer">
          {t(language, "footerLine1")} {t(language, "footerLine2")}{" "}
          {t(language, "footerLine3")}
        </footer>
      </main>
    </div>
  );
}
