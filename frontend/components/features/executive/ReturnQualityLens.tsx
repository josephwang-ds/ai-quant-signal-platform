"use client";

import Link from "next/link";
import MetricCard from "@/components/ui/MetricCard";
import SectionHeader from "@/components/ui/SectionHeader";
import { returnQualityMetrics } from "@/lib/mockQuantData";
import {
  formatMetricPercent,
  formatMetricSharpe,
  getDrawdownTone,
  getReturnTone,
  getSharpeTone,
} from "@/lib/formatters";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

type ReturnQualityLensProps = {
  showModuleLink?: boolean;
};

export default function ReturnQualityLens({ showModuleLink = true }: ReturnQualityLensProps) {
  const { tr } = useWorkspaceLanguage();
  const metrics = returnQualityMetrics;

  return (
    <section className="return-quality-lens">
      <SectionHeader
        title={tr("returnQualityLens")}
        description={tr("returnQualityLensModuleNote")}
      />
      <div className="metric-grid return-quality-lens__grid">
        <MetricCard
          label={tr("totalReturn")}
          value={formatMetricPercent(metrics.totalReturn)}
          tone={getReturnTone(metrics.totalReturn)}
        />
        <MetricCard
          label={tr("benchmarkReturn")}
          value={formatMetricPercent(metrics.benchmarkReturn)}
          tone={getReturnTone(metrics.benchmarkReturn)}
        />
        <MetricCard
          label={tr("returnQualityExcessReturn")}
          value={formatMetricPercent(metrics.excessReturn)}
          tone={getReturnTone(metrics.excessReturn)}
        />
        <MetricCard
          label={tr("returnQualityMaxDrawdown")}
          value={formatMetricPercent(metrics.maxDrawdown)}
          tone={getDrawdownTone(metrics.maxDrawdown)}
        />
        <MetricCard
          label={tr("sharpeRatio")}
          value={formatMetricSharpe(metrics.sharpeRatio)}
          tone={getSharpeTone(metrics.sharpeRatio)}
        />
        <MetricCard
          label={tr("returnQualityCostDrag")}
          value={formatMetricPercent(metrics.costDrag)}
          tone="negative"
        />
        <MetricCard
          label={tr("returnQualityHitRate")}
          value={formatMetricPercent(metrics.hitRate)}
        />
        <MetricCard
          label={tr("returnQualityProfitFactor")}
          value={metrics.profitFactor.toFixed(2)}
          tone={metrics.profitFactor >= 1 ? "accent" : "default"}
        />
        <MetricCard
          label={tr("returnQualityCapitalAtRisk")}
          value={`$${metrics.capitalAtRisk.toLocaleString()}`}
          tone="negative"
        />
        <MetricCard
          label={tr("returnQualityDrawdownBuffer")}
          value={formatMetricPercent(metrics.drawdownBufferToRed)}
          tone={metrics.drawdownBufferToRed >= 0.02 ? "default" : "negative"}
        />
      </div>
      <p className="section-meta return-quality-lens__note">{tr("returnQualityLensSimulatedNote")}</p>
      {showModuleLink ? (
        <Link href="/return-quality-lens" className="module-card__link">
          {tr("openModule")} →
        </Link>
      ) : null}
    </section>
  );
}
