"use client";

import DataTable from "@/components/ui/DataTable";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { decisionLedgerEntries } from "@/lib/mockQuantData";
import {
  paperRiskVariant,
  translateBackendText,
  translatePaperAction,
  translateRiskLabel,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

function riskLevelToNumber(label: string): number {
  switch (label) {
    case "Green":
      return 1;
    case "Light Yellow":
      return 2;
    case "Yellow":
      return 3;
    case "Orange":
      return 4;
    case "Red":
      return 5;
    default:
      return 2;
  }
}

function actionVariant(action: string): "buy" | "sell" | "neutral" | "warning" {
  if (action.includes("BUY") || action.includes("ADD")) {
    return "buy";
  }
  if (action.includes("SELL") || action.includes("REDUCE")) {
    return "sell";
  }
  if (action.includes("HOLD") || action.includes("NO ACTION") || action.includes("MAINTAIN")) {
    return "warning";
  }
  return "neutral";
}

export default function DecisionLedgerPanel() {
  const { language, tr } = useWorkspaceLanguage();

  return (
    <SectionCard>
      <SectionHeader title={tr("decisionLedger")} description={tr("decisionLedgerDesc")} />
      <p className="section-meta">{tr("decisionLedgerNote")}</p>

      <DataTable className="table-scroll--ledger">
        <thead>
          <tr>
            <th>{tr("ledgerDate")}</th>
            <th>{tr("ledgerSymbol")}</th>
            <th>{tr("ledgerStrategy")}</th>
            <th>{tr("ledgerRawSignal")}</th>
            <th>{tr("ledgerRiskLevel")}</th>
            <th>{tr("ledgerGateDecision")}</th>
            <th>{tr("ledgerFinalPaperAction")}</th>
            <th>{tr("ledgerExplanation")}</th>
            <th>{tr("ledgerHumanNote")}</th>
            <th>{tr("ledgerOutcome")}</th>
          </tr>
        </thead>
        <tbody>
          {decisionLedgerEntries.map((entry) => (
            <tr key={entry.id}>
              <td>{entry.date}</td>
              <td>{entry.symbol}</td>
              <td>{entry.strategy}</td>
              <td>
                <StatusBadge
                  label={translatePaperAction(language, entry.rawSignal)}
                  variant={actionVariant(entry.rawSignal)}
                />
              </td>
              <td>
                <StatusBadge
                  label={translateRiskLabel(language, entry.riskLevel)}
                  variant={paperRiskVariant(riskLevelToNumber(entry.riskLevel))}
                />
              </td>
              <td>{translateBackendText(language, entry.gateDecision)}</td>
              <td>
                <StatusBadge
                  label={translateBackendText(language, entry.finalPaperAction)}
                  variant={actionVariant(entry.finalPaperAction)}
                />
              </td>
              <td className="ledger-cell-text">
                {translateBackendText(language, entry.explanation)}
              </td>
              <td className="ledger-cell-text ledger-cell-text--human">
                {translateBackendText(language, entry.humanNote)}
              </td>
              <td className="ledger-cell-text">
                {translateBackendText(language, entry.outcome)}
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </SectionCard>
  );
}
