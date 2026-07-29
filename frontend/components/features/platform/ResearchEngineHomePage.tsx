"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { CANONICAL_RESEARCH_ID } from "@/lib/canonicalMaCrossover";
import { CANONICAL_FACTOR_RESEARCH_ID } from "@/lib/canonicalCrossSectionalFactor";
import {
  ENGINE_STAGES,
  FLAGSHIP_RESEARCH,
  UNIVERSE_PREVIEW_SYMBOLS,
  US_LIQUID_31_SYMBOLS,
  getContinueTarget,
  stageStatusLabel,
  type EngineStage,
} from "@/lib/platformArchitecture";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const COPY = {
  en: {
    productLabel: "Quant Research Engine",
    continueLabel: "Continue",
    continueHint: "Opens the next available stage. Locked stages remain viewable for planning.",
    configTitle: "Current research configuration",
    workflowTitle: "Ordered research workflow",
    workflowHint:
      "One path. Completed stages keep evidence; the current stage is where work continues; locked stages wait on prior evidence.",
    openStage: "Open stage detail",
    legacyTitle: "Legacy demonstration",
    legacyBody:
      "Trend Following remains available as a single-asset demo. It is not the flagship engine path.",
    legacyCta: "Open Trend Following demo",
    universeSummary: "US Liquid 31 · 31 symbols · Static demo universe",
    universePreviewSuffix: "+25",
    universeAll: "All symbols",
    universeDisclosure:
      "Manually configured demonstration universe — not a point-in-time index membership set. Survivorship bias is not corrected.",
    systemNote:
      "Browser-local research state may apply. This shell does not invent Phase 4 portfolio or PnL results.",
    interactiveFactor: "Open interactive Factor Study path",
  },
  zh: {
    productLabel: "量化研究引擎",
    continueLabel: "继续",
    continueHint: "进入下一个可用阶段。锁定阶段仍可查看以便规划。",
    configTitle: "当前研究配置",
    workflowTitle: "有序研究工作流",
    workflowHint:
      "只有一条主线。已完成阶段保留证据；当前阶段是继续位置；锁定阶段等待前置证据。",
    openStage: "打开阶段详情",
    legacyTitle: "遗留演示",
    legacyBody: "趋势跟踪仍可作为单标的演示，但不是旗舰引擎路径。",
    legacyCta: "打开趋势跟踪演示",
    universeSummary: "US Liquid 31 · 31 只标的 · 静态演示股票池",
    universePreviewSuffix: "+25",
    universeAll: "全部标的",
    universeDisclosure:
      "人工配置的演示股票池，不是时点指数成分集，也不处理幸存者偏差。",
    systemNote: "研究状态可能仅保存在浏览器。本壳层不虚构 Phase 4 组合或 PnL 结果。",
    interactiveFactor: "打开交互式因子研究路径",
  },
} as const;

function stageClass(status: EngineStage["status"]): string {
  if (status === "completed") return "is-completed";
  if (status === "current") return "is-current";
  return "is-locked";
}

export default function ResearchEngineHomePage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const copy = COPY[language];
  const continueTarget = getContinueTarget();

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="research-flow" data-testid="research-engine-home">
        <header className="research-flow__hero" data-testid="research-flow-hero">
          <div>
            <p className="research-flow__product-label">{copy.productLabel}</p>
            <h1>
              {language === "zh" ? FLAGSHIP_RESEARCH.nameZh : FLAGSHIP_RESEARCH.nameEn}
            </h1>
            <p className="research-flow__lede">
              {FLAGSHIP_RESEARCH.universe} ·{" "}
              {language === "zh"
                ? FLAGSHIP_RESEARCH.dataFrequencyZh
                : FLAGSHIP_RESEARCH.dataFrequencyEn}{" "}
              ·{" "}
              {language === "zh"
                ? FLAGSHIP_RESEARCH.factorsZh
                : FLAGSHIP_RESEARCH.factorsEn}{" "}
              ·{" "}
              {language === "zh"
                ? FLAGSHIP_RESEARCH.labelsZh
                : FLAGSHIP_RESEARCH.labelsEn}
            </p>
            <p className="research-flow__progress">
              {language === "zh"
                ? FLAGSHIP_RESEARCH.verifiedThroughZh
                : FLAGSHIP_RESEARCH.verifiedThroughEn}{" "}
              · {language === "zh" ? FLAGSHIP_RESEARCH.nextZh : FLAGSHIP_RESEARCH.nextEn}
            </p>
          </div>
          <div className="research-flow__continue-wrap">
            <Link
              href={`/engine/${continueTarget.id}`}
              className="btn btn--primary"
              data-testid="workflow-continue"
            >
              {copy.continueLabel}:{" "}
              {language === "zh" ? continueTarget.titleZh : continueTarget.titleEn}
            </Link>
            <p>{copy.continueHint}</p>
          </div>
        </header>

        <section
          className="research-flow__config"
          data-testid="current-research-config"
        >
          <h2>{copy.configTitle}</h2>
          <dl>
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
              <dt>{language === "zh" ? "下一阶段" : "Next stage"}</dt>
              <dd data-testid="next-stage-name">
                {language === "zh"
                  ? continueTarget.titleZh
                  : continueTarget.titleEn}
              </dd>
            </div>
          </dl>
          <details className="research-flow__universe" data-testid="universe-details">
            <summary>
              <span>{copy.universeSummary}</span>
              <span className="research-flow__universe-preview">
                {UNIVERSE_PREVIEW_SYMBOLS.join(" · ")} · {copy.universePreviewSuffix}
              </span>
            </summary>
            <div className="research-flow__universe-body">
              <p className="research-flow__universe-title">{copy.universeAll}</p>
              <ul className="research-flow__symbols">
                {US_LIQUID_31_SYMBOLS.map((symbol) => (
                  <li key={symbol}>
                    <code>{symbol}</code>
                  </li>
                ))}
              </ul>
              <p className="research-flow__disclosure">{copy.universeDisclosure}</p>
            </div>
          </details>
        </section>

        <section
          className="research-flow__workflow"
          data-testid="guided-workflow"
        >
          <header>
            <h2>{copy.workflowTitle}</h2>
            <p>{copy.workflowHint}</p>
          </header>
          <ol className="research-flow__steps">
            {ENGINE_STAGES.map((stage) => (
              <li key={stage.id}>
                <Link
                  href={`/engine/${stage.id}`}
                  className={`research-flow__step ${stageClass(stage.status)}`}
                  data-testid={`workflow-step-${stage.id}`}
                  data-status={stage.status}
                >
                  <span className="research-flow__step-index">{stage.number}</span>
                  <span className="research-flow__step-copy">
                    <strong>
                      {language === "zh" ? stage.titleZh : stage.titleEn}
                    </strong>
                    <em>{stageStatusLabel(stage.status, language)}</em>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </section>

        <p className="research-flow__stage-actions">
          <Link
            href={`/engine/research/${encodeURIComponent(CANONICAL_FACTOR_RESEARCH_ID)}`}
            className="btn"
          >
            {copy.interactiveFactor}
          </Link>
        </p>

        <aside className="research-flow__legacy" data-testid="legacy-trend-demo">
          <div>
            <p className="research-flow__legacy-kicker">{copy.legacyTitle}</p>
            <p>{copy.legacyBody}</p>
          </div>
          <Link
            href={`/engine/research/${encodeURIComponent(CANONICAL_RESEARCH_ID)}`}
            className="btn"
            data-testid="open-trend-demo"
          >
            {copy.legacyCta}
          </Link>
        </aside>

        <p className="research-flow__system-note">{copy.systemNote}</p>
      </div>
    </AppShell>
  );
}
