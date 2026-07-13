"use client";

import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  MOCK_COCKPIT_SNAPSHOT,
  decisionRoomSignalSnapshot,
  returnQualityMetrics,
} from "@/lib/mockQuantData";
import {
  formatMetricPercent,
  formatMetricSharpe,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

/** 策略健康度评分面板（模拟数据，供管理层演示） */
export default function StrategyHealthScorePanel() {
  const { language, tr } = useWorkspaceLanguage();
  const snapshot = MOCK_COCKPIT_SNAPSHOT;
  const quality = returnQualityMetrics;
  const signal = decisionRoomSignalSnapshot;

  const pillars =
    language === "zh"
      ? [
          { label: "收益质量", score: 78, note: "超额收益为正，但成本拖累需持续跟踪。" },
          { label: "回撤控制", score: 72, note: "最大回撤 -8.6%，距红色闸口仍有缓冲。" },
          { label: "风险闸口", score: 70, note: "当前 Yellow / L3，限制新开模拟仓。" },
          { label: "信号稳定性", score: 74, note: "Momentum 原始信号 BUY，经闸口降级为 HOLD ONLY。" },
        ]
      : [
          { label: "Return quality", score: 78, note: "Positive excess return; cost drag needs monitoring." },
          { label: "Drawdown control", score: 72, note: "Max drawdown -8.6% with buffer remaining to Red." },
          { label: "Risk gates", score: 70, note: "Yellow / L3 — new simulated entries restricted." },
          { label: "Signal stability", score: 74, note: "Momentum raw BUY downgraded by gates to HOLD ONLY." },
        ];

  return (
    <>
      <SectionCard>
        <SectionHeader
          title={tr("strategyHealthScore")}
          description={tr("strategyHealthScoreDesc")}
        />
        <p className="section-meta">{tr("cockpitDisclaimer")}</p>
        <div className="metric-grid">
          <MetricCard
            label={tr("strategyHealthScore")}
            value={`${snapshot.healthScore} / 100`}
            featured
          />
          <MetricCard
            label={tr("sharpeRatio")}
            value={formatMetricSharpe(quality.sharpeRatio)}
            tone={getSharpeTone(quality.sharpeRatio)}
          />
          <MetricCard
            label={tr("returnQualityMaxDrawdown")}
            value={formatMetricPercent(quality.maxDrawdown)}
            tone={getDrawdownTone(quality.maxDrawdown)}
          />
          <MetricCard
            label={tr("returnQualityExcessReturn")}
            value={formatMetricPercent(quality.excessReturn)}
            tone={getReturnTone(quality.excessReturn)}
          />
        </div>
        <div className="decision-room__badges" style={{ marginTop: "1rem" }}>
          <StatusBadge label={`${signal.symbol} · ${signal.strategy}`} variant="neutral" />
          <StatusBadge label={`Score ${snapshot.healthScore}`} variant="buy" />
        </div>
      </SectionCard>

      <SectionCard>
        <SectionHeader
          title={language === "zh" ? "分项评分" : "Score pillars"}
          description={
            language === "zh"
              ? "综合分由收益、回撤、闸口与信号稳定性加权合成（演示口径）。"
              : "Composite score blends return, drawdown, gates, and signal stability (demo weights)."
          }
        />
        <div className="decision-room__roles">
          {pillars.map((pillar) => (
            <article key={pillar.label} className="decision-room__role">
              <h3 className="decision-room__role-title">
                {pillar.label} · {pillar.score}/100
              </h3>
              <p className="section-meta">{pillar.note}</p>
            </article>
          ))}
        </div>
      </SectionCard>
    </>
  );
}
