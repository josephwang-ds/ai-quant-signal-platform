"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import {
  ENGINE_STAGES,
  FLAGSHIP_RESEARCH,
  INTELLIGENCE_MODULES,
  PLATFORM,
  getContinueTarget,
  stageStatusLabel,
} from "@/lib/platformArchitecture";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function PlatformHomePage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const continueTarget = getContinueTarget();
  const completedCount = ENGINE_STAGES.filter((s) => s.status === "completed").length;

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="platform-home" data-testid="platform-home">
        <header className="platform-home__hero" data-testid="platform-home-hero">
          <p className="platform-home__eyebrow">
            {language === "zh" ? "产品层" : "Product layer"}
          </p>
          <h1>{language === "zh" ? PLATFORM.nameZh : PLATFORM.nameEn}</h1>
          <p className="platform-home__tagline" data-testid="product-tagline">
            {language === "zh" ? PLATFORM.taglineZh : PLATFORM.taglineEn}
          </p>
          <p className="platform-home__principle" data-testid="product-philosophy">
            {language === "zh" ? PLATFORM.principleZh : PLATFORM.principleEn}
          </p>
          <div className="platform-home__cta-row">
            <Link href="/engine" className="btn btn--primary" data-testid="open-research-engine">
              {language === "zh" ? "进入研究引擎" : "Open Research Engine"}
            </Link>
            <Link
              href={`/engine/${continueTarget.id}`}
              className="btn"
              data-testid="continue-engine-stage"
            >
              {language === "zh"
                ? `继续：${continueTarget.titleZh}`
                : `Continue: ${continueTarget.titleEn}`}
            </Link>
          </div>
        </header>

        <section
          className="platform-home__intelligence"
          aria-labelledby="intelligence-grid-title"
          data-testid="intelligence-grid"
        >
          <header>
            <h2 id="intelligence-grid-title">
              {language === "zh" ? "AI 投资智能" : "AI Investment Intelligence"}
            </h2>
            <p>
              {language === "zh"
                ? "回答「发生了什么」。每张卡片都必须可追溯到研究引擎证据——不发布无依据结论。"
                : "Answers “what is happening?” Every card must be traceable to Research Engine evidence — no unsupported conclusions."}
            </p>
          </header>
          <ul className="platform-home__cards">
            {INTELLIGENCE_MODULES.map((module) => (
              <li key={module.id}>
                <Link
                  href={module.href}
                  className="platform-home__card"
                  data-testid={`intelligence-card-${module.id}`}
                >
                  <strong>
                    {language === "zh" ? module.titleZh : module.titleEn}
                  </strong>
                  <span>
                    {language === "zh" ? module.questionZh : module.questionEn}
                  </span>
                  <em>{language === "zh" ? module.statusZh : module.statusEn}</em>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section
          className="platform-home__engine-status"
          aria-labelledby="engine-status-title"
          data-testid="research-engine-status"
        >
          <header>
            <h2 id="engine-status-title">
              {language === "zh" ? "研究引擎状态" : "Research Engine Status"}
            </h2>
            <p>
              {language === "zh"
                ? "回答「为什么」。旗舰配置与阶段进度如下。"
                : "Answers “why?” Flagship configuration and stage progress below."}
            </p>
          </header>
          <dl className="platform-home__config">
            <div>
              <dt>{language === "zh" ? "研究" : "Research"}</dt>
              <dd>
                {language === "zh"
                  ? FLAGSHIP_RESEARCH.nameZh
                  : FLAGSHIP_RESEARCH.nameEn}
              </dd>
            </div>
            <div>
              <dt>{language === "zh" ? "股票池" : "Universe"}</dt>
              <dd>{FLAGSHIP_RESEARCH.universe}</dd>
            </div>
            <div>
              <dt>{language === "zh" ? "进度" : "Progress"}</dt>
              <dd data-testid="engine-progress">
                {completedCount}/{ENGINE_STAGES.length}{" "}
                {language === "zh" ? "已完成" : "completed"} ·{" "}
                {language === "zh"
                  ? FLAGSHIP_RESEARCH.verifiedThroughZh
                  : FLAGSHIP_RESEARCH.verifiedThroughEn}
              </dd>
            </div>
            <div>
              <dt>{language === "zh" ? "当前阶段" : "Current stage"}</dt>
              <dd data-testid="engine-current-stage">
                {language === "zh"
                  ? continueTarget.titleZh
                  : continueTarget.titleEn}
              </dd>
            </div>
          </dl>
          <ol className="platform-home__stage-strip" data-testid="engine-stage-strip">
            {ENGINE_STAGES.map((stage) => (
              <li key={stage.id} data-status={stage.status}>
                <Link href={`/engine/${stage.id}`}>
                  <span>{stage.number}</span>
                  <strong>
                    {language === "zh" ? stage.titleZh : stage.titleEn}
                  </strong>
                  <em>{stageStatusLabel(stage.status, language)}</em>
                </Link>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </AppShell>
  );
}
