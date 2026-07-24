"use client";

import Link from "next/link";
import { t, type Language } from "@/lib/i18n";

type GuidedReviewEntryProps = {
  language: Language;
  href: string;
};

/**
 * Reviewer-first product entry.
 * It frames the product around one evidence trail instead of asking visitors
 * to infer the story from a catalogue of modules.
 */
export default function GuidedReviewEntry({
  language,
  href,
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
      <div className="guided-review-entry__intro">
        <p className="guided-review-entry__eyebrow">
          {t(language, "guidedReviewEyebrow")}
        </p>
        <h2 id="guided-review-entry-title">
          {t(language, "guidedReviewTitle")}
        </h2>
        <p>{t(language, "guidedReviewDescription")}</p>
        <Link href={href} className="btn btn--primary">
          {t(language, "guidedReviewStart")}
        </Link>
      </div>

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

      <div className="guided-review-entry__difference">
        <p>{t(language, "guidedReviewDifferenceTitle")}</p>
        <ul
          className="guided-review-entry__trust"
          aria-label={t(language, "guidedReviewTrustLabel")}
        >
          <li>{t(language, "guidedReviewTrustSource")}</li>
          <li>{t(language, "guidedReviewTrustDeterministic")}</li>
          <li>{t(language, "guidedReviewTrustUnknowns")}</li>
          <li>{t(language, "guidedReviewTrustHuman")}</li>
        </ul>
      </div>
    </section>
  );
}
