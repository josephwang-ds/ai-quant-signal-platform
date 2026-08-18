"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { PRODUCT_REPO_URL } from "@/lib/productIdentity";
import {
  PRICE_BASELINE,
  STANDING_LIMITATIONS,
  SUBTRACTION_LADDER,
  TEXT_SIGNAL_EXPERIMENTS,
  completedStepCount,
  experimentStatusLabel,
} from "@/lib/textSignalsArchitecture";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

const LIMITATIONS_DOC = `${PRODUCT_REPO_URL}/blob/main/docs/KNOWN_LIMITATIONS.md`;

export default function TextSignalsHomePage() {
  const { language, setLanguage } = useWorkspaceLanguage();
  const zh = language === "zh";

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <div className="text-signals" data-testid="text-signals-home">
        <header className="text-signals__hero">
          <p className="text-signals__eyebrow">
            {zh ? "研究轨道" : "Research track"}
          </p>
          <h1>{zh ? "文本信号" : "Text Signals"}</h1>
          <p className="text-signals__tagline">
            {zh
              ? "信号通道是文本（SEC 申报文件），不是价格；所测量的是相对纯价格基线的增量信息价值，不是超额收益。"
              : "The signal channel is text (SEC filings), not price. The measured quantity is incremental information value over a price-only baseline, not excess return."}
          </p>
          <p className="text-signals__scope-line">
            {zh
              ? "结果尚未产生 · 状态如实标注 · 不预写示例数字"
              : "No results yet · status stated honestly · no example figures pre-written"}
          </p>
        </header>

        <section className="text-signals__panel" aria-labelledby="ladder-title">
          <h2 id="ladder-title">
            {zh ? "所测量的量" : "The quantity being measured"}
          </h2>
          <p className="text-signals__panel-note">
            {zh
              ? "每一层减去一个竞争性解释。全部减完之后剩下的，才是关心的量。"
              : "Each rung removes a competing explanation. What survives all of them is the quantity of interest."}
          </p>
          <ol className="text-signals__ladder">
            {SUBTRACTION_LADDER.map((rung, index) => (
              <li
                key={index}
                className={
                  "terminal" in rung && rung.terminal
                    ? "text-signals__rung text-signals__rung--terminal"
                    : "text-signals__rung"
                }
              >
                <code>{zh ? rung.subtractZh : rung.subtractEn}</code>
                <span aria-hidden="true">→</span>
                <strong>{zh ? rung.yieldsZh : rung.yieldsEn}</strong>
              </li>
            ))}
          </ol>
          <p className="text-signals__panel-note">
            {zh
              ? "这样做把一个无法回答的问题（「这能跑赢市场吗？」）换成一个可以回答的问题（「这个文本通道相对价格是否增加了信息？」）——两个分支覆盖相同时期、承担相同交易假设，成本在对比中大致抵消。"
              : "This converts an unanswerable question (“does this beat the market?”) into an answerable one (“does this text channel add information over price?”), because both arms span the same periods and carry the same trading assumptions, so cost largely cancels in the contrast."}
          </p>
        </section>

        <section
          className="text-signals__experiments"
          aria-labelledby="experiments-title"
          data-testid="text-signals-experiments"
        >
          <h2 id="experiments-title">
            {zh ? "三个实验" : "The three experiments"}
          </h2>
          <ul className="text-signals__experiment-list">
            {TEXT_SIGNAL_EXPERIMENTS.map((experiment) => {
              const done = completedStepCount(experiment);
              const total = experiment.steps?.length ?? 0;
              return (
                <li key={experiment.id}>
                  <article
                    className="text-signals__experiment"
                    data-status={experiment.status}
                    data-testid={`experiment-${experiment.id}`}
                  >
                    <header className="text-signals__experiment-head">
                      <span className="text-signals__experiment-id">
                        {experiment.id}
                      </span>
                      <div>
                        <h3>{zh ? experiment.titleZh : experiment.titleEn}</h3>
                        <p className="text-signals__experiment-role">
                          {zh ? experiment.roleZh : experiment.roleEn}
                        </p>
                      </div>
                      <span
                        className={`text-signals__status text-signals__status--${experiment.status}`}
                      >
                        {experimentStatusLabel(experiment.status, language)}
                        {total > 0 ? ` · ${done}/${total}` : ""}
                      </span>
                    </header>

                    <p className="text-signals__experiment-question">
                      {zh ? experiment.questionZh : experiment.questionEn}
                    </p>

                    {experiment.steps ? (
                      <ol className="text-signals__steps">
                        {experiment.steps.map((step) => (
                          <li
                            key={step.id}
                            data-done={step.done ? "true" : "false"}
                          >
                            <span
                              className={`text-signals__step-dot${
                                step.done
                                  ? " text-signals__step-dot--done"
                                  : ""
                              }`}
                              aria-hidden="true"
                            />
                            <code>{step.id}</code>
                            <span>{zh ? step.labelZh : step.labelEn}</span>
                          </li>
                        ))}
                      </ol>
                    ) : null}

                    <p className="text-signals__experiment-status-note">
                      {zh ? experiment.statusNoteZh : experiment.statusNoteEn}
                    </p>
                  </article>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="text-signals__panel" aria-labelledby="baseline-title">
          <h2 id="baseline-title">
            {zh ? "对照臂：纯价格基线" : "The control arm: price-only baseline"}
          </h2>
          <p className="text-signals__panel-note">
            {zh ? PRICE_BASELINE.bodyZh : PRICE_BASELINE.bodyEn}
          </p>
          <Link
            href={PRICE_BASELINE.href}
            className="btn"
            data-testid="open-price-baseline"
          >
            {zh ? "打开价格基线" : "Open the price baseline"}
          </Link>
        </section>

        <section
          className="text-signals__panel"
          aria-labelledby="limitations-title"
          data-testid="text-signals-limitations"
        >
          <h2 id="limitations-title">
            {zh ? "随结果同行的限制" : "Constraints that travel with any result"}
          </h2>
          <dl className="text-signals__limitations">
            {STANDING_LIMITATIONS.map((limitation) => (
              <div key={limitation.id}>
                <dt>
                  <code>{limitation.id}</code>{" "}
                  {zh ? limitation.titleZh : limitation.titleEn}
                </dt>
                <dd>{zh ? limitation.bodyZh : limitation.bodyEn}</dd>
              </div>
            ))}
          </dl>
          <a
            className="text-signals__doc-link"
            href={LIMITATIONS_DOC}
            target="_blank"
            rel="noopener noreferrer"
          >
            {zh
              ? "完整已知限制清单（含生存者偏差与前视控制）→"
              : "Full known-limitations list (survivorship bias, look-ahead controls) →"}
          </a>
        </section>
      </div>
    </AppShell>
  );
}
