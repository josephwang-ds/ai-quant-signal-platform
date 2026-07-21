import type { ReactNode } from "react";

type EmptyStateProps = {
  /** Legacy single-line hint — rendered as description when title is absent. */
  message?: string;
  /** Why nothing is shown. */
  title?: string;
  /** What the user should do next. */
  description?: string;
  action?: ReactNode;
};

/**
 * Canonical empty state: explain why empty + what to do next.
 * Prefer title + description; `message` alone maps to description.
 */
export default function EmptyState({
  message,
  title,
  description,
  action,
}: EmptyStateProps) {
  const resolvedTitle = title;
  const resolvedDescription = description ?? message ?? null;

  return (
    <div className="empty-state-panel" role="status">
      {resolvedTitle ? (
        <h3 className="empty-state-panel__title">{resolvedTitle}</h3>
      ) : null}
      {resolvedDescription ? (
        <p className="empty-state-panel__description">{resolvedDescription}</p>
      ) : null}
      {action ? <div className="empty-state-panel__action">{action}</div> : null}
    </div>
  );
}
