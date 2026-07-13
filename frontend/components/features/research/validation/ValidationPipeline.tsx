import type { Language } from "@/lib/i18n";
import type { ValidationStage } from "@/types/validation";
import ValidationStageCard, {
  type ValidationStageCardLabels,
} from "./ValidationStageCard";

export type ValidationPipelineLabels = {
  title: string;
  card: ValidationStageCardLabels;
};

type ValidationPipelineProps = {
  stages: ValidationStage[];
  language: Language;
  labels: ValidationPipelineLabels;
  selectedStageId: string | null;
  onSelectStage: (id: string) => void;
};

/**
 * Ordered validation stage pipeline list.
 * TODO(backend): stages ordered by Validation Application policy.
 */
export default function ValidationPipeline({
  stages,
  language,
  labels,
  selectedStageId,
  onSelectStage,
}: ValidationPipelineProps) {
  return (
    <section className="validation-pipeline" aria-label={labels.title}>
      <h3 className="validation-pipeline__title">{labels.title}</h3>
      <div className="validation-pipeline__list">
        {stages.map((stage) => (
          <ValidationStageCard
            key={stage.id}
            stage={stage}
            language={language}
            labels={labels.card}
            selected={stage.id === selectedStageId}
            onSelect={onSelectStage}
          />
        ))}
      </div>
    </section>
  );
}
