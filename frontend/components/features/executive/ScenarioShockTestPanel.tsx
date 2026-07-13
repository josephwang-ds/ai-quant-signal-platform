"use client";

import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { scenarioShockScenarios } from "@/lib/mockQuantData";
import { paperRiskVariant, translateBackendText, translateRiskLabel } from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

function riskLevelToNumber(label: string): number {
  switch (label) {
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

export default function ScenarioShockTestPanel() {
  const { language, tr } = useWorkspaceLanguage();

  return (
    <>
      <SectionCard>
        <SectionHeader
          title={tr("scenarioShockTest")}
          description={tr("scenarioShockTestDesc")}
        />
        <p className="section-meta">{tr("scenarioShockTestNote")}</p>
      </SectionCard>

      {scenarioShockScenarios.map((scenario) => (
        <SectionCard key={scenario.id}>
          <SectionHeader title={translateBackendText(language, scenario.title)} />
          <div className="scenario-shock__metrics">
            <div className="scenario-shock__metric">
              <span className="scenario-shock__label">{tr("scenarioShockNavImpact")}</span>
              <span className="scenario-shock__value">{scenario.navImpact}</span>
            </div>
            <div className="scenario-shock__metric">
              <span className="scenario-shock__label">{tr("scenarioShockRiskAfter")}</span>
              <StatusBadge
                label={translateRiskLabel(language, scenario.riskLevelAfter)}
                variant={paperRiskVariant(riskLevelToNumber(scenario.riskLevelAfter))}
              />
            </div>
          </div>

          <h4 className="paper-subtitle">{tr("scenarioShockTriggeredRules")}</h4>
          <ul className="paper-reason-list">
            {scenario.triggeredRules.map((rule) => (
              <li key={rule}>{translateBackendText(language, rule)}</li>
            ))}
          </ul>

          <h4 className="paper-subtitle">{tr("scenarioShockSystemAction")}</h4>
          <p className="section-meta">
            {translateBackendText(language, scenario.systemAction)}
          </p>

          <h4 className="paper-subtitle">{tr("scenarioShockInterpretation")}</h4>
          <p className="section-meta scenario-shock__interpretation">
            {translateBackendText(language, scenario.managementInterpretation)}
          </p>
        </SectionCard>
      ))}
    </>
  );
}
