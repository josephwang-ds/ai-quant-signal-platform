"use client";

import {
  benchmarkLabel,
  researchDefinitionTextLabel,
  researchHypothesisLabel,
  researchQuestionLabel,
} from "@/lib/researchDisplay";
import type { Language } from "@/lib/i18n";
import type { ResearchDetail } from "@/types/research";

export type ResearchDefinitionSummaryLabels = {
  title: string;
  researchQuestion: string;
  hypothesis: string;
  dataUniverse: string;
  evaluationProtocol: string;
  successCriteria: string;
  knownLimitations: string;
  unavailable: string;
};

type Props = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchDefinitionSummaryLabels;
};

function findParameter(research: ResearchDetail, keys: string[]): string | null {
  const lines = research.configuration.parameterLines;
  for (const key of keys) {
    const match = lines.find((line) =>
      line.toLowerCase().startsWith(key.toLowerCase())
    );
    if (match) {
      const idx = match.indexOf(":");
      return idx >= 0 ? match.slice(idx + 1).trim() : match;
    }
  }
  return null;
}

export default function ResearchDefinitionSummary({
  research,
  language,
  labels,
}: Props) {
  const protocolLine =
    findParameter(research, ["Evaluation Protocol", "评估协议"]) ??
    research.configuration.parameterLines.slice(0, 3).join(" · ");
  const protocol = protocolLine || labels.unavailable;
  const success =
    findParameter(research, ["Success Criteria", "成功标准"]) ??
    labels.unavailable;
  const dataUniverse = [
    research.configuration.symbol,
    benchmarkLabel(research.configuration.benchmark, language),
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <section
      className="research-definition-summary"
      aria-labelledby="research-definition-summary-title"
    >
      <h3 id="research-definition-summary-title">{labels.title}</h3>
      <dl className="research-definition-summary__dl">
        <div>
          <dt>{labels.researchQuestion}</dt>
          <dd>
            {researchQuestionLabel(
              research.id,
              research.researchQuestion,
              language
            ) || labels.unavailable}
          </dd>
        </div>
        <div>
          <dt>{labels.hypothesis}</dt>
          <dd>
            {researchHypothesisLabel(
              research.id,
              research.hypothesis,
              language
            ) || labels.unavailable}
          </dd>
        </div>
        <div>
          <dt>{labels.dataUniverse}</dt>
          <dd>{dataUniverse || labels.unavailable}</dd>
        </div>
        <div>
          <dt>{labels.evaluationProtocol}</dt>
          <dd>{researchDefinitionTextLabel(protocol, language)}</dd>
        </div>
        <div>
          <dt>{labels.successCriteria}</dt>
          <dd>{researchDefinitionTextLabel(success, language)}</dd>
        </div>
        <div>
          <dt>{labels.knownLimitations}</dt>
          <dd>
            {research.knownWeaknesses.length > 0 ? (
              <ul>
                {research.knownWeaknesses.map((item) => (
                  <li key={item}>
                    {researchDefinitionTextLabel(item, language)}
                  </li>
                ))}
              </ul>
            ) : (
              labels.unavailable
            )}
          </dd>
        </div>
      </dl>
    </section>
  );
}
