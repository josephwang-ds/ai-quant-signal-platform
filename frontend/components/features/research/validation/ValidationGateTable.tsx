import StatusBadge, { passFailVariant } from "@/components/ui/StatusBadge";
import type { ValidationGate } from "@/types/validation";

export type ValidationGateTableLabels = {
  title: string;
  rule: string;
  threshold: string;
  observed: string;
  result: string;
  severity: string;
  evidence: string;
  pass: string;
  fail: string;
  empty: string;
  deterministicNote: string;
};

type ValidationGateTableProps = {
  gates: ValidationGate[];
  labels: ValidationGateTableLabels;
};

export default function ValidationGateTable({
  gates,
  labels,
}: ValidationGateTableProps) {
  return (
    <section className="validation-gates" aria-label={labels.title}>
      <h4 className="validation-gates__title">{labels.title}</h4>
      <p className="section-meta">{labels.deterministicNote}</p>
      {gates.length === 0 ? (
        <p className="validation-gates__empty">{labels.empty}</p>
      ) : (
        <div className="validation-gates__table-wrap">
          <table className="validation-gates__table">
            <thead>
              <tr>
                <th scope="col">{labels.rule}</th>
                <th scope="col">{labels.threshold}</th>
                <th scope="col">{labels.observed}</th>
                <th scope="col">{labels.result}</th>
                <th scope="col">{labels.severity}</th>
                <th scope="col">{labels.evidence}</th>
              </tr>
            </thead>
            <tbody>
              {gates.map((gate) => (
                <tr key={gate.id}>
                  <td>{gate.rule}</td>
                  <td className="font-mono">{gate.threshold}</td>
                  <td className="font-mono">{gate.observed}</td>
                  <td>
                    <StatusBadge
                      label={gate.passed ? labels.pass : labels.fail}
                      variant={passFailVariant(gate.passed)}
                    />
                  </td>
                  <td>{gate.severity}</td>
                  <td className="font-mono">{gate.evidenceRef}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
