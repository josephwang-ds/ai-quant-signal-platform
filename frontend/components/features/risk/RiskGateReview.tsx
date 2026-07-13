"use client";

import Link from "next/link";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import { riskGateReviewFlow } from "@/lib/mockQuantData";
import {
  translateBackendText,
  translateConfidence,
  translatePaperAction,
  translateRiskLabel,
} from "@/lib/i18n";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

type RiskGateReviewProps = {
  showModuleLink?: boolean;
};

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

export default function RiskGateReview({ showModuleLink = true }: RiskGateReviewProps) {
  const { language, tr } = useWorkspaceLanguage();
  const flow = riskGateReviewFlow;

  return (
    <section className="risk-gate-review">
      <SectionHeader
        title={tr("riskGateReview")}
        description={tr("riskGateReviewModuleNote")}
      />

      <div className="risk-gate-review__flow">
        <article className="risk-gate-review__step">
          <h3 className="risk-gate-review__step-title">{tr("riskGateStepStrategySignal")}</h3>
          <dl className="paper-kv paper-kv--compact">
            <div>
              <dt>{tr("riskGateRawSignal")}</dt>
              <dd>
                <StatusBadge
                  label={translatePaperAction(language, flow.strategySignal.rawSignal)}
                  variant={signalVariant(flow.strategySignal.rawSignal)}
                />
              </dd>
            </div>
            <div>
              <dt>{tr("strategy")}</dt>
              <dd>{flow.strategySignal.strategy}</dd>
            </div>
            <div>
              <dt>{tr("paperConfidence")}</dt>
              <dd>{translateConfidence(language, flow.strategySignal.confidence)}</dd>
            </div>
          </dl>
        </article>

        <div className="risk-gate-review__arrow" aria-hidden="true">
          →
        </div>

        <article className="risk-gate-review__step risk-gate-review__step--gate">
          <h3 className="risk-gate-review__step-title">{tr("riskGateStepGateReview")}</h3>
          <dl className="paper-kv paper-kv--compact">
            <div>
              <dt>{tr("riskGateRiskLevel")}</dt>
              <dd>
                <StatusBadge
                  label={translateRiskLabel(language, flow.riskGate.riskLevel)}
                  variant="warning"
                />
              </dd>
            </div>
            <div>
              <dt>{tr("riskGateDecision")}</dt>
              <dd>{translateBackendText(language, flow.riskGate.gateDecision)}</dd>
            </div>
          </dl>
          <h4 className="paper-subtitle">{tr("riskGateReasons")}</h4>
          <ul className="paper-reason-list">
            {flow.riskGate.reasons.map((reason) => (
              <li key={reason}>{translateBackendText(language, reason)}</li>
            ))}
          </ul>
        </article>

        <div className="risk-gate-review__arrow" aria-hidden="true">
          →
        </div>

        <article className="risk-gate-review__step risk-gate-review__step--final">
          <h3 className="risk-gate-review__step-title">{tr("riskGateStepFinalAction")}</h3>
          <StatusBadge
            label={translateBackendText(language, flow.finalAction.action)}
            variant={signalVariant(flow.finalAction.action)}
          />
          <p className="section-meta risk-gate-review__final-note">
            {translateBackendText(language, flow.finalAction.note)}
          </p>
        </article>
      </div>

      <p className="section-meta risk-gate-review__note">{tr("riskGateSimulatedNote")}</p>
      {showModuleLink ? (
        <Link href="/risk-gate-review" className="module-card__link">
          {tr("openModule")} →
        </Link>
      ) : null}
    </section>
  );
}
