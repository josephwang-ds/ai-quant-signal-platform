"use client";

import MetricCard from "@/components/ui/MetricCard";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  decisionRoomRetrievedContext,
  decisionRoomReviewQuestions,
  decisionRoomRoles,
  decisionRoomSignalSnapshot,
} from "@/lib/mockQuantData";
import {
  paperRiskVariant,
  translateBackendText,
  translatePaperAction,
  translateRiskLabel,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

function signalVariant(signal: string): "buy" | "sell" | "neutral" | "warning" {
  switch (signal) {
    case "BUY":
      return "buy";
    case "SELL":
      return "sell";
    case "HOLD ONLY":
      return "warning";
    default:
      return "neutral";
  }
}

export default function DecisionRoomPanel() {
  const { language, tr } = useWorkspaceLanguage();
  const snapshot = decisionRoomSignalSnapshot;

  return (
    <>
      <SectionCard>
        <SectionHeader title={tr("decisionRoom")} description={tr("decisionRoomDesc")} />
        <p className="section-meta">{tr("decisionRoomNote")}</p>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("decisionRoomSignalSnapshot")} />
        <div className="metric-grid decision-room__snapshot">
          <MetricCard label={tr("ledgerSymbol")} value={snapshot.symbol} />
          <MetricCard label={tr("ledgerStrategy")} value={snapshot.strategy} />
          <MetricCard
            label={tr("ledgerRawSignal")}
            value={translatePaperAction(language, snapshot.rawSignal)}
          />
          <MetricCard
            label={tr("ledgerRiskLevel")}
            value={translateRiskLabel(language, snapshot.riskLevel)}
          />
          <MetricCard
            label={tr("ledgerGateDecision")}
            value={translateBackendText(language, snapshot.gateDecision)}
          />
          <MetricCard
            label={tr("ledgerFinalPaperAction")}
            value={translateBackendText(language, snapshot.finalPaperAction)}
          />
          <MetricCard
            label={tr("strategyHealthScore")}
            value={`${snapshot.strategyHealthScore} / 100`}
            featured
          />
        </div>
        <div className="decision-room__badges">
          <StatusBadge
            label={translatePaperAction(language, snapshot.rawSignal)}
            variant={signalVariant(snapshot.rawSignal)}
          />
          <StatusBadge
            label={translateRiskLabel(language, snapshot.riskLevel)}
            variant={paperRiskVariant(3)}
          />
          <StatusBadge
            label={translateBackendText(language, snapshot.finalPaperAction)}
            variant="warning"
          />
        </div>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("decisionRoomRolesTitle")} />
        <div className="decision-room__roles">
          {decisionRoomRoles.map((role) => (
            <article key={role.id} className="decision-room__role">
              <h3 className="decision-room__role-title">
                {translateBackendText(language, role.title)}
              </h3>
              <p className="section-meta">
                {translateBackendText(language, role.explanation)}
              </p>
            </article>
          ))}
        </div>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("decisionRoomRetrievedContext")} />
        <ul className="decision-room__context-list">
          {decisionRoomRetrievedContext.map((item) => (
            <li key={item.id} className="decision-room__context-item">
              <span className="decision-room__context-source">
                {translateBackendText(language, item.source)}:
              </span>{" "}
              {translateBackendText(language, item.text)}
            </li>
          ))}
        </ul>
        <p className="section-meta">{tr("decisionRoomRagNote")}</p>
      </SectionCard>

      <SectionCard>
        <SectionHeader title={tr("decisionRoomReviewQuestions")} />
        <ul className="paper-reason-list">
          {decisionRoomReviewQuestions.map((question) => (
            <li key={question}>{translateBackendText(language, question)}</li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}
