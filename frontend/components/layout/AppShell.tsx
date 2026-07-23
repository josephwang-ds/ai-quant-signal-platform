"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import type { Language } from "@/lib/i18n";
import { t } from "@/lib/i18n";
import {
  getBackendReadinessState,
  subscribeBackendReadiness,
  warmBackend,
  type BackendReadinessState,
} from "@/lib/apiRequest";
import {
  PRODUCT_COPYRIGHT,
  PRODUCT_REPO_URL,
  PRODUCT_VERSION,
} from "@/lib/productIdentity";
import DemoBanner from "./DemoBanner";
import LanguageToggle from "./LanguageToggle";
import SideNav from "./SideNav";
import TopNav from "./TopNav";

type AppShellProps = {
  language: Language;
  onLanguageChange: (language: Language) => void;
  children: ReactNode;
};

const MOBILE_NAV_MQ = "(max-width: 767px)";

export default function AppShell({
  language,
  onLanguageChange,
  children,
}: AppShellProps) {
  const pathname = usePathname();
  const [navOpen, setNavOpen] = useState(false);
  const [isMobileNav, setIsMobileNav] = useState(false);
  const [backendReadiness, setBackendReadiness] =
    useState<BackendReadinessState>(getBackendReadinessState);

  useEffect(() => {
    const media = window.matchMedia(MOBILE_NAV_MQ);
    const sync = () => setIsMobileNav(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (process.env.NODE_ENV === "test") return;
    const unsubscribe = subscribeBackendReadiness(setBackendReadiness);
    void warmBackend().catch(() => undefined);
    return unsubscribe;
  }, []);

  useEffect(() => {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  }, [language]);

  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!isMobileNav) setNavOpen(false);
  }, [isMobileNav]);

  useEffect(() => {
    if (!navOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setNavOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navOpen]);

  useEffect(() => {
    if (!navOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [navOpen]);

  const drawerHidden = isMobileNav && !navOpen;

  return (
    <div className={`workspace-shell${navOpen ? " is-nav-open" : ""}`}>
      <TopNav
        language={language}
        onLanguageChange={onLanguageChange}
        navOpen={navOpen}
        onToggleNav={() => setNavOpen((open) => !open)}
      />

      {navOpen ? (
        <button
          type="button"
          className="workspace-nav-overlay"
          aria-label={t(language, "navCloseMenu")}
          onClick={() => setNavOpen(false)}
        />
      ) : null}

      <aside
        id="workspace-sidebar"
        className="workspace-sidebar"
        aria-hidden={drawerHidden || undefined}
        {...(drawerHidden ? ({ inert: true } as { inert: boolean }) : {})}
      >
        <Link href="/overview" className="workspace-brand">
          <span className="workspace-brand__name">{t(language, "appTitleShort")}</span>
          <span className="workspace-brand__version">v{PRODUCT_VERSION}</span>
        </Link>
        <SideNav language={language} onNavigate={() => setNavOpen(false)} />
        <div className="workspace-sidebar__footer">
          <LanguageToggle language={language} onLanguageChange={onLanguageChange} />
        </div>
      </aside>

      <main className="workspace-main">
        <DemoBanner language={language} />
        {backendReadiness === "waking" || backendReadiness === "unavailable" ? (
          <aside
            className={`backend-startup backend-startup--${backendReadiness}`}
            role={backendReadiness === "unavailable" ? "alert" : "status"}
            aria-live="polite"
          >
            <div>
              <strong>
                {t(
                  language,
                  backendReadiness === "waking"
                    ? "backendStarting"
                    : "backendStartupUnavailable"
                )}
              </strong>
              <span>
                {t(
                  language,
                  backendReadiness === "waking"
                    ? "backendStartingHint"
                    : "backendStartupUnavailableHint"
                )}
              </span>
            </div>
            {backendReadiness === "unavailable" ? (
              <button
                type="button"
                className="btn"
                onClick={() => {
                  void warmBackend({ force: true }).catch(() => undefined);
                }}
              >
                {t(language, "backendStartupRetry")}
              </button>
            ) : null}
          </aside>
        ) : null}
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
