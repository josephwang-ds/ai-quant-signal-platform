"use client";

import Link from "next/link";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import { PRODUCT_VERSION } from "@/lib/productIdentity";

type TopNavProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
  navOpen: boolean;
  onToggleNav: () => void;
};

/**
 * Mobile top bar — brand + menu toggle. Desktop navigation stays in SideNav.
 */
export default function TopNav({
  language,
  onLanguageChange,
  navOpen,
  onToggleNav,
}: TopNavProps) {
  return (
    <header className="workspace-topbar">
      <button
        type="button"
        className="workspace-topbar__menu"
        aria-expanded={navOpen}
        aria-controls="workspace-sidebar"
        onClick={onToggleNav}
      >
        <span className="workspace-topbar__menu-icon" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
        <span className="workspace-topbar__menu-label">
          {t(language, navOpen ? "navCloseMenu" : "navOpenMenu")}
        </span>
      </button>

      <Link href="/overview" className="workspace-brand workspace-brand--compact">
        <span className="workspace-brand__name">{t(language, "appTitleShort")}</span>
        <span className="workspace-brand__version">v{PRODUCT_VERSION}</span>
      </Link>

      <div className="workspace-topbar__actions">
        <button
          type="button"
          className="workspace-language-switch"
          aria-label={language === "en" ? "切换为中文" : "Switch to English"}
          title={language === "en" ? "切换为中文" : "Switch to English"}
          onClick={() => onLanguageChange(language === "en" ? "zh" : "en")}
        >
          {language === "en" ? "中" : "EN"}
        </button>
      </div>
    </header>
  );
}
