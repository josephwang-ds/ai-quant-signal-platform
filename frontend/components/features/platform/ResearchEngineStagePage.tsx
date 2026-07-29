"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { CANONICAL_FACTOR_RESEARCH_ID } from "@/lib/canonicalCrossSectionalFactor";
import {
  ENGINE_STAGES,
  getContinueTarget,
  getEngineStage,
  stageStatusLabel,
  type EngineStageId,
} from "@/lib/platformArchitecture";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const SECTION_LABELS = {
  en: {
    purpose: "Purpose",
    inputs: "Inputs",
    methods: "Methods",
    outputs: "Outputs",
    evidence: "Evidence",
    limitations: "Known Limitations",
    next: "Next Stage",
    absorbs: "Includes former experiment work",
    tools: "Existing tools",
    back: "Engine overview",
    continue: "Continue to next available stage",
    interactive: "Open interactive Factor Study path",
  },
  zh: {
    purpose: "目的",
    inputs: "输入",
    methods: "方法",
    outputs: "输出",
    evidence: "证据",
    limitations: "已知限制",
    next: "下一阶段",
    absorbs: "承接原实验类内容",
    tools: "现有工具",
    back: "引擎总览",
    continue: "继续到下一可用阶段",
    interactive: "打开交互式因子研究路径",
  },
} as const;

type Props = {
  stageId: EngineStageId;
};

export default function ResearchEngineStagePage({ stageId }: Props) {
  const { language, setLanguage } = useWorkspaceLanguage();
  const labels = SECTION_LABELS[language];
  const stage = getEngineStage(stageId);
  const continueTarget = getContinueTarget();
  const stageIndex = ENGINE_STAGES.findIndex((item) => item.id === stageId);
  const nextStage =
    stageIndex >= 0 && stageIndex < ENGINE_STAGES.length - 1
      ? ENGINE_STAGES[stageIndex + 1]
      : undefined;

  if (!stage) {
    return (
      <AppShell language={language} onLanguageChange={setLanguage}>
        <p>Unknown engine stage.</p>
      </AppShell>
    );
  }

  const list = (items: readonly string[]) => (
    <ul>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <article
        className="engine-stage"
        data-testid="engine-stage-page"
        data-stage={stage.id}
        data-status={stage.status}
      >
        <header className="engine-stage__hero">
          <p>
            {stage.number}. {stageStatusLabel(stage.status, language)}
          </p>
          <h1>{language === "zh" ? stage.titleZh : stage.titleEn}</h1>
          <p>{language === "zh" ? stage.purposeZh : stage.purposeEn}</p>
          <div className="engine-stage__nav">
            <Link href="/engine" className="btn">
              {labels.back}
            </Link>
            <Link
              href={`/engine/${continueTarget.id}`}
              className="btn btn--primary"
              data-testid="engine-stage-continue"
            >
              {labels.continue}:{" "}
              {language === "zh" ? continueTarget.titleZh : continueTarget.titleEn}
            </Link>
          </div>
        </header>

        <section>
          <h2>{labels.purpose}</h2>
          <p>{language === "zh" ? stage.purposeZh : stage.purposeEn}</p>
        </section>
        <section>
          <h2>{labels.inputs}</h2>
          {list(language === "zh" ? stage.inputsZh : stage.inputsEn)}
        </section>
        <section>
          <h2>{labels.methods}</h2>
          {list(language === "zh" ? stage.methodsZh : stage.methodsEn)}
        </section>
        <section>
          <h2>{labels.outputs}</h2>
          {list(language === "zh" ? stage.outputsZh : stage.outputsEn)}
        </section>
        <section data-testid="engine-stage-evidence">
          <h2>{labels.evidence}</h2>
          {list(language === "zh" ? stage.evidenceZh : stage.evidenceEn)}
        </section>
        <section>
          <h2>{labels.limitations}</h2>
          {list(language === "zh" ? stage.limitationsZh : stage.limitationsEn)}
        </section>

        {(stage.absorbsEn?.length ?? 0) > 0 ? (
          <section>
            <h2>{labels.absorbs}</h2>
            {list(language === "zh" ? stage.absorbsZh ?? [] : stage.absorbsEn ?? [])}
          </section>
        ) : null}

        {(stage.toolHrefs?.length ?? 0) > 0 ? (
          <section>
            <h2>{labels.tools}</h2>
            <ul className="engine-stage__tools">
              {stage.toolHrefs?.map((tool) => (
                <li key={tool.href}>
                  <Link href={tool.href} className="btn">
                    {language === "zh" ? tool.labelZh : tool.labelEn}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {stage.id === "factors" || stage.id === "modeling" ? (
          <p>
            <Link
              href={`/engine/research/${encodeURIComponent(CANONICAL_FACTOR_RESEARCH_ID)}`}
              className="btn"
            >
              {labels.interactive}
            </Link>
          </p>
        ) : null}

        <section data-testid="engine-stage-next">
          <h2>{labels.next}</h2>
          {nextStage ? (
            <p>
              <Link href={`/engine/${nextStage.id}`}>
                {nextStage.number}.{" "}
                {language === "zh" ? nextStage.titleZh : nextStage.titleEn} (
                {stageStatusLabel(nextStage.status, language)})
              </Link>
            </p>
          ) : (
            <p>{language === "zh" ? "工作流终点。" : "End of workflow."}</p>
          )}
        </section>
      </article>
    </AppShell>
  );
}
