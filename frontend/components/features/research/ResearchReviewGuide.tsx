"use client";

import Link from "next/link";
import { t, type Language } from "@/lib/i18n";
import type { ResearchWorkspaceSection } from "@/types/research";

type ReviewStep = {
  id: "question" | "evidence" | "challenge" | "decision";
  section: ResearchWorkspaceSection;
  label: string;
  cue: string;
};

type ResearchReviewGuideProps = {
  researchId: string;
  activeSection: ResearchWorkspaceSection;
  language: Language;
};

function reviewStepIndex(section: ResearchWorkspaceSection): number {
  if (section === "validation" || section === "evaluation") return 1;
  if (section === "robustness" || section === "paper") return 2;
  if (section === "decision") return 3;
  return 0;
}

function sectionHref(
  researchId: string,
  section: ResearchWorkspaceSection,
  reviewMode: boolean
): string {
  const base = `/research/${encodeURIComponent(researchId)}`;
  const params = new URLSearchParams();
  if (section !== "overview") params.set("tab", section);
  if (reviewMode) params.set("review", "1");
  const query = params.toString();
  return query ? `${base}?${query}` : base;
}

/**
 * Four-stop narrative overlay for interview and customer review.
 * It changes navigation only; evidence and lifecycle state remain authoritative.
 */
export default function ResearchReviewGuide({
  researchId,
  activeSection,
  language,
}: ResearchReviewGuideProps) {
  const steps: ReviewStep[] = [
    {
      id: "question",
      section: "overview",
      label: t(language, "guidedReviewStepQuestion"),
      cue: t(language, "researchReviewCueQuestion"),
    },
    {
      id: "evidence",
      section: "validation",
      label: t(language, "guidedReviewStepEvidence"),
      cue: t(language, "researchReviewCueEvidence"),
    },
    {
      id: "challenge",
      section: "robustness",
      label: t(language, "guidedReviewStepChallenge"),
      cue: t(language, "researchReviewCueChallenge"),
    },
    {
      id: "decision",
      section: "decision",
      label: t(language, "guidedReviewStepDecision"),
      cue: t(language, "researchReviewCueDecision"),
    },
  ];
  const activeIndex = reviewStepIndex(activeSection);
  const activeStep = steps[activeIndex];
  const nextStep = steps[activeIndex + 1] ?? null;

  return (
    <aside
      className="research-review-guide"
      aria-labelledby="research-review-guide-title"
      data-testid="research-review-guide"
    >
      <div className="research-review-guide__header">
        <div>
          <p className="research-review-guide__eyebrow">
            {t(language, "researchReviewMode")}
          </p>
          <h2 id="research-review-guide-title">
            {t(language, "researchReviewProgress")
              .replace("{current}", String(activeIndex + 1))
              .replace("{total}", String(steps.length))}
          </h2>
        </div>
        <Link
          href={sectionHref(researchId, activeSection, false)}
          className="research-review-guide__exit"
        >
          {t(language, "researchReviewExit")}
        </Link>
      </div>

      <ol className="research-review-guide__steps">
        {steps.map((step, index) => (
          <li
            key={step.id}
            className={[
              index === activeIndex ? "is-current" : "",
              index < activeIndex ? "is-complete" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <Link href={sectionHref(researchId, step.section, true)}>
              <span aria-hidden="true">
                {index < activeIndex ? "✓" : index + 1}
              </span>
              {step.label}
            </Link>
          </li>
        ))}
      </ol>

      <div className="research-review-guide__cue">
        <span>{t(language, "researchReviewSay")}</span>
        <p>{activeStep.cue}</p>
        {nextStep ? (
          <Link
            href={sectionHref(researchId, nextStep.section, true)}
            className="btn btn--primary"
          >
            {t(language, "researchReviewNext").replace(
              "{step}",
              nextStep.label
            )}
          </Link>
        ) : (
          <Link href="/" className="btn btn--primary">
            {t(language, "researchReviewFinish")}
          </Link>
        )}
      </div>
    </aside>
  );
}
