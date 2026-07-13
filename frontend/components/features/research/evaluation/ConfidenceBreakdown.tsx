import {
  computeResearchConfidence,
  computeWeightedContribution,
} from "@/lib/researchEvaluation";
import type { EvaluationDimension } from "@/types/evaluation";
import EvaluationDimensionStatusBadge from "./EvaluationDimensionStatusBadge";

export type ConfidenceBreakdownLabels = {
  title: string;
  formula: string;
  dimension: string;
  score: string;
  weight: string;
  contribution: string;
  status: string;
  total: string;
  weightsTotal: string;
};

type ConfidenceBreakdownProps = {
  dimensions: EvaluationDimension[];
  labels: ConfidenceBreakdownLabels;
  weightsTotal: number;
};

export default function ConfidenceBreakdown({
  dimensions,
  labels,
  weightsTotal,
}: ConfidenceBreakdownProps) {
  const total = computeResearchConfidence(dimensions);

  return (
    <section className="confidence-breakdown" aria-label={labels.title}>
      <h3 className="confidence-breakdown__title">{labels.title}</h3>
      <p className="section-meta">{labels.formula}</p>
      <p className="section-meta">
        {labels.weightsTotal}: <span className="font-mono">{weightsTotal}</span>
      </p>
      <div className="confidence-breakdown__table-wrap">
        <table className="confidence-breakdown__table">
          <thead>
            <tr>
              <th scope="col">{labels.dimension}</th>
              <th scope="col">{labels.score}</th>
              <th scope="col">{labels.weight}</th>
              <th scope="col">{labels.contribution}</th>
              <th scope="col">{labels.status}</th>
            </tr>
          </thead>
          <tbody>
            {dimensions.map((dimension) => (
              <tr key={dimension.key}>
                <td>{dimension.name}</td>
                <td className="font-mono">{dimension.score}</td>
                <td className="font-mono">{dimension.weight}</td>
                <td className="font-mono">
                  {computeWeightedContribution(
                    dimension.score,
                    dimension.weight
                  ).toFixed(2)}
                </td>
                <td>
                  <EvaluationDimensionStatusBadge status={dimension.status} />
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row">{labels.total}</th>
              <td colSpan={2} />
              <td className="font-mono">{total}</td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>
    </section>
  );
}
