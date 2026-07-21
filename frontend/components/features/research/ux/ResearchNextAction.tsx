"use client";

import type { ReactNode } from "react";
import Button from "@/components/ui/Button";

export type ResearchNextActionProps = {
  /** Eyebrow caption — e.g. "Next action" */
  eyebrow: string;
  title: string;
  description?: string;
  cta?: string;
  onClick?: () => void;
  disabled?: boolean;
  /** Optional trailing content below the CTA. */
  footer?: ReactNode;
};

/**
 * Shared Next Action panel used across lifecycle pages.
 * Same layout / CTA style as Overview NextStepPanel.
 */
export default function ResearchNextAction({
  eyebrow,
  title,
  description,
  cta,
  onClick,
  disabled = false,
  footer = null,
}: ResearchNextActionProps) {
  return (
    <aside className="next-step-panel" aria-label={eyebrow}>
      <div className="next-step-panel__accent" aria-hidden="true" />
      <div className="next-step-panel__body">
        <p className="next-step-panel__eyebrow">{eyebrow}</p>
        <h3 className="next-step-panel__title">{title}</h3>
        {description ? (
          <p className="next-step-panel__description section-meta">{description}</p>
        ) : null}
        {cta ? (
          <Button primary disabled={disabled || !onClick} onClick={onClick}>
            {cta}
          </Button>
        ) : null}
        {footer}
      </div>
    </aside>
  );
}
