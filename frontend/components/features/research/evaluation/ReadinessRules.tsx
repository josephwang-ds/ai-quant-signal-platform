import StatusBadge, { passFailVariant } from "@/components/ui/StatusBadge";
import type { EvaluationRuleCheck } from "@/types/evaluation";

export type ReadinessRulesLabels = {
  title: string;
  description: string;
  rule: string;
  observed: string;
  result: string;
  pass: string;
  fail: string;
};

type ReadinessRulesProps = {
  rules: EvaluationRuleCheck[];
  labels: ReadinessRulesLabels;
};

export default function ReadinessRules({ rules, labels }: ReadinessRulesProps) {
  return (
    <section className="readiness-rules" aria-label={labels.title}>
      <h3 className="readiness-rules__title">{labels.title}</h3>
      <p className="section-meta">{labels.description}</p>
      <div className="readiness-rules__table-wrap">
        <table className="readiness-rules__table">
          <thead>
            <tr>
              <th scope="col">{labels.rule}</th>
              <th scope="col">{labels.observed}</th>
              <th scope="col">{labels.result}</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((rule) => (
              <tr key={rule.id}>
                <td>{rule.rule}</td>
                <td className="font-mono">{rule.observed}</td>
                <td>
                  <StatusBadge
                    label={rule.passed ? labels.pass : labels.fail}
                    variant={passFailVariant(rule.passed)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
