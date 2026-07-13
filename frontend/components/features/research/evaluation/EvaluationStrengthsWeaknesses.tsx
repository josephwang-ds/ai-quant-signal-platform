import type { EvaluationStrengthWeakness } from "@/types/evaluation";

export type EvaluationStrengthsWeaknessesLabels = {
  title: string;
  strengths: string;
  weaknesses: string;
  empty: string;
};

type EvaluationStrengthsWeaknessesProps = {
  items: EvaluationStrengthWeakness[];
  labels: EvaluationStrengthsWeaknessesLabels;
};

export default function EvaluationStrengthsWeaknesses({
  items,
  labels,
}: EvaluationStrengthsWeaknessesProps) {
  const strengths = items.filter((item) => item.kind === "strength");
  const weaknesses = items.filter((item) => item.kind === "weakness");

  return (
    <section
      className="evaluation-sw"
      aria-label={labels.title}
    >
      <h3 className="evaluation-sw__title">{labels.title}</h3>
      <div className="evaluation-sw__grid">
        <div>
          <h4>{labels.strengths}</h4>
          {strengths.length === 0 ? (
            <p className="section-meta">{labels.empty}</p>
          ) : (
            <ul>
              {strengths.map((item) => (
                <li key={item.id}>
                  {item.text}
                  <span className="font-mono"> ({item.evidenceRef})</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <h4>{labels.weaknesses}</h4>
          {weaknesses.length === 0 ? (
            <p className="section-meta">{labels.empty}</p>
          ) : (
            <ul>
              {weaknesses.map((item) => (
                <li key={item.id}>
                  {item.text}
                  <span className="font-mono"> ({item.evidenceRef})</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
