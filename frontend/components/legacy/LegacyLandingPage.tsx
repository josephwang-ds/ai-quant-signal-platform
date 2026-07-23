"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const DESTINATIONS = [
  { href: "/", en: "Research Library", zh: "研究库" },
  { href: "/strategy-lab", en: "Strategy Studio", zh: "策略工作室" },
  { href: "/market-watch", en: "AI Watchlist", zh: "AI 关注列表" },
  { href: "/compare-models", en: "Model Comparison", zh: "模型对比" },
] as const;

export default function LegacyLandingPage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const zh = language === "zh";

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard className="legacy-landing-hero">
        <SectionHeader
          level={1}
          title={zh ? "旧版工作台已完成迁移" : "Legacy workspace migrated"}
          description={
            zh
              ? "原始综合仪表盘已拆分为更清晰的研究、实验、证据与审阅工作流。"
              : "The original all-in-one dashboard has been decomposed into clearer research, experiment, evidence, and review workflows."
          }
        />
      </SectionCard>

      <SectionCard className="legacy-landing-panel">
        <p className="legacy-landing-panel__intro">
          {zh
            ? "旧组件源码仍保留用于迁移参考。请选择当前产品入口继续。"
            : "The legacy component remains in the repository for migration reference. Continue from a current product surface."}
        </p>
        <nav className="legacy-destination-grid" aria-label={zh ? "当前产品入口" : "Current product destinations"}>
          {DESTINATIONS.map((destination) => (
            <Link key={destination.href} href={destination.href}>
              <span>{zh ? destination.zh : destination.en}</span>
              <span aria-hidden="true">→</span>
            </Link>
          ))}
        </nav>
      </SectionCard>
    </AppShell>
  );
}
