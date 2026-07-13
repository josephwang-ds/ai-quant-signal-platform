"use client";

import MetricCard from "@/components/ui/MetricCard";
import { MOCK_COCKPIT_SNAPSHOT } from "@/lib/mockQuantData";
import { getDrawdownTone, getReturnTone } from "@/lib/formatters";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

export default function ExecutiveCockpitSnapshot() {
  const { tr } = useWorkspaceLanguage();
  const snapshot = MOCK_COCKPIT_SNAPSHOT;

  return (
    <div className="metric-grid cockpit-snapshot">
      <MetricCard
        label={tr("cockpitNav")}
        value={`$${snapshot.portfolioNav.toLocaleString()}`}
      />
      <MetricCard
        label={tr("cockpitYtdReturn")}
        value={`${snapshot.ytdReturnPct.toFixed(2)}%`}
        tone={getReturnTone(snapshot.ytdReturnPct / 100)}
      />
      <MetricCard
        label={tr("cockpitMaxDrawdown")}
        value={`${snapshot.maxDrawdownPct.toFixed(1)}%`}
        tone={getDrawdownTone(snapshot.maxDrawdownPct / 100)}
      />
      <MetricCard label={tr("cockpitSharpe")} value={snapshot.sharpeRatio.toFixed(2)} />
      <MetricCard label={tr("cockpitRiskLevel")} value={`L${snapshot.riskLevel}`} />
      <MetricCard label={tr("strategyHealthScore")} value={`${snapshot.healthScore}/100`} />
    </div>
  );
}
