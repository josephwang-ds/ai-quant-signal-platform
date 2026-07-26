import { t, type Language } from "@/lib/i18n";

type GuidedReviewEntryProps = {
  language: Language;
};

/**
 * Reviewer-first product entry.
 * It frames the product around one evidence trail instead of asking visitors
 * to infer the story from a catalogue of modules.
 */
export default function GuidedReviewEntry({
  language,
}: GuidedReviewEntryProps) {
  const steps = [
    {
      label: t(language, "guidedReviewStepQuestion"),
      detail: t(language, "guidedReviewStepQuestionDetail"),
    },
    {
      label: t(language, "guidedReviewStepEvidence"),
      detail: t(language, "guidedReviewStepEvidenceDetail"),
    },
    {
      label: t(language, "guidedReviewStepChallenge"),
      detail: t(language, "guidedReviewStepChallengeDetail"),
    },
    {
      label: t(language, "guidedReviewStepDecision"),
      detail: t(language, "guidedReviewStepDecisionDetail"),
    },
  ];

  return (
    <section
      className="guided-review-entry"
      aria-labelledby="guided-review-entry-title"
      data-testid="guided-review-entry"
    >
      <header className="guided-review-entry__intro">
        <p className="guided-review-entry__eyebrow">
          {t(language, "guidedReviewEyebrow")}
        </p>
        <h2 id="guided-review-entry-title">
          {t(language, "guidedReviewTitle")}
        </h2>
        <p>{t(language, "guidedReviewDescription")}</p>
      </header>

      <ol className="guided-review-entry__steps">
        {steps.map((step, index) => (
          <li key={step.label}>
            <span className="guided-review-entry__index" aria-hidden="true">
              {index + 1}
            </span>
            <div>
              <strong>{step.label}</strong>
              <span>{step.detail}</span>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
