"use client";

import type { ResearchReadinessModel } from "@/lib/researchReadiness";

export type ResearchReadinessLabels = {
  title: string;
  description: string;
  yes: string;
  no: string;
  researchQuestion: string;
  hypothesis: string;
  protocol: string;
  validation: string;
  robustness: string;
  decision: string;
  limitations: string;
};

type Props = {
  model: ResearchReadinessModel;
  labels: ResearchReadinessLabels;
};

const LABEL_BY_ID: Record<
  ResearchReadinessModel["items"][number]["id"],
  keyof ResearchReadinessLabels
> = {
  research_question: "researchQuestion",
  hypothesis: "hypothesis",
  protocol: "protocol",
  validation: "validation",
  robustness: "robustness",
  decision: "decision",
  limitations: "limitations",
};

export default function ResearchReadinessSummary({ model, labels }: Props) {
  return (
    <section
      className="research-readiness"
      aria-labelledby="research-readiness-title"
    >
      <h3 id="research-readiness-title">{labels.title}</h3>
      <p className="section-meta">{labels.description}</p>
      <ul className="research-readiness__list">
        {model.items.map((item) => (
          <li key={item.id}>
            <span>{labels[LABEL_BY_ID[item.id]]}</span>
            <strong data-complete={item.complete ? "yes" : "no"}>
              {item.complete ? labels.yes : labels.no}
            </strong>
          </li>
        ))}
      </ul>
      <p className="section-meta">
        {model.completedCount}/{model.totalCount}
      </p>
    </section>
  );
}
