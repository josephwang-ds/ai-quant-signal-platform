"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import {
  getIntelligenceModule,
  type IntelligenceModuleId,
} from "@/lib/platformArchitecture";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const COPY = {
  en: {
    layer: "AI Investment Intelligence",
    evidencePath: "Evidence path",
    openEngine: "Open linked Research Engine stage",
    noOpinion:
      "This surface does not invent AI opinions. When evidence is missing, the status stays explicit.",
    existingTools: "Existing research tools",
  },
  zh: {
    layer: "AI 投资智能",
    evidencePath: "证据路径",
    openEngine: "打开关联的研究引擎阶段",
    noOpinion: "本页不虚构 AI 观点。证据缺失时，状态保持明确披露。",
    existingTools: "现有研究工具",
  },
} as const;

const EXISTING_TOOL_LINKS: Partial<
  Record<IntelligenceModuleId, { href: string; labelEn: string; labelZh: string }[]>
> = {
  market: [
    { href: "/market-watch", labelEn: "Market Watch (rule scores)", labelZh: "市场观察（规则评分）" },
  ],
  assistant: [
    { href: "/ai-insights", labelEn: "AI Insights / news sentiment panel", labelZh: "AI 洞察 / 新闻情绪面板" },
  ],
  research: [{ href: "/engine", labelEn: "Research Engine overview", labelZh: "研究引擎总览" }],
  signal: [
    { href: "/engine/modeling", labelEn: "Modeling evidence", labelZh: "建模证据" },
    { href: "/compare-models", labelEn: "Model comparison utility", labelZh: "模型对比工具" },
  ],
  portfolio: [
    { href: "/engine/portfolio", labelEn: "Portfolio Construction stage", labelZh: "组合构建阶段" },
  ],
  risk: [
    { href: "/engine/backtest", labelEn: "Backtesting stage", labelZh: "回测阶段" },
    { href: "/robustness", labelEn: "Robustness utilities", labelZh: "稳健性工具" },
  ],
};

type Props = {
  moduleId: IntelligenceModuleId;
};

export default function IntelligenceModulePage({ moduleId }: Props) {
  const { language, setLanguage } = useWorkspaceLanguage();
  const copy = COPY[language];
  const module = getIntelligenceModule(moduleId);
  const tools = EXISTING_TOOL_LINKS[moduleId] ?? [];

  if (!module) {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <p>Unknown intelligence module.</p>
      </AppShell>
    );
  }

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <article
        className="intelligence-page"
        data-testid="intelligence-page"
        data-module={module.id}
      >
        <header className="intelligence-page__hero">
          <p className="intelligence-page__layer">{copy.layer}</p>
          <h1>{language === "zh" ? module.titleZh : module.titleEn}</h1>
          <p>{language === "zh" ? module.questionZh : module.questionEn}</p>
        </header>

        <section className="intelligence-page__status" data-testid="intelligence-status">
          <h2>{language === "zh" ? "当前状态" : "Current status"}</h2>
          <p>{language === "zh" ? module.statusZh : module.statusEn}</p>
          <p className="intelligence-page__note">{copy.noOpinion}</p>
        </section>

        <section className="intelligence-page__path">
          <h2>{copy.evidencePath}</h2>
          <p data-testid="intelligence-evidence-path">
            {language === "zh" ? module.evidencePathZh : module.evidencePathEn}
          </p>
          <Link href={module.engineHref} className="btn btn--primary">
            {copy.openEngine}
          </Link>
        </section>

        {tools.length > 0 ? (
          <section className="intelligence-page__tools">
            <h2>{copy.existingTools}</h2>
            <ul>
              {tools.map((tool) => (
                <li key={tool.href}>
                  <Link href={tool.href} className="btn">
                    {language === "zh" ? tool.labelZh : tool.labelEn}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </article>
    </AppShell>
  );
}
