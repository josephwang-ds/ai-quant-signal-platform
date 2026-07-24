"use client";

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
    research.configuration.benchmark,
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
          <dd>{research.researchQuestion || labels.unavailable}</dd>
        </div>
        <div>
          <dt>{labels.hypothesis}</dt>
          <dd>{research.hypothesis || labels.unavailable}</dd>
        </div>
        <div>
          <dt>{labels.dataUniverse}</dt>
          <dd>{dataUniverse || labels.unavailable}</dd>
        </div>
        <div>
          <dt>{labels.evaluationProtocol}</dt>
          <dd>{protocol}</dd>
        </div>
        <div>
          <dt>{labels.successCriteria}</dt>
          <dd>{success}</dd>
        </div>
        <div>
          <dt>{labels.knownLimitations}</dt>
          <dd>
            {research.knownWeaknesses.length > 0 ? (
              <ul>
                {research.knownWeaknesses.map((item) => (
                  <li key={item}>{item}</li>
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
