/**
 * Shared published-workspace skeleton for route loading, Suspense fallback,
 * and client gate loading — keeps layout stable across the handoff.
 */
export type PublishedWorkspaceSkeletonProps = {
  /** Optional status message for assistive tech (rendered outside aria-hidden). */
  statusLabel?: string;
  testId?: string;
};

export default function PublishedWorkspaceSkeleton({
  statusLabel,
  testId = "published-workspace-loading",
}: PublishedWorkspaceSkeletonProps) {
  return (
    <div
      className="published-workspace published-workspace--fallback"
      data-testid={testId}
      aria-busy="true"
    >
      <div className="published-workspace__loading" aria-hidden="true">
        <div className="research-skeleton research-skeleton--title" />
        <div className="research-skeleton research-skeleton--line" />
        <div className="published-workspace__nav-skeleton">
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index} className="research-skeleton research-skeleton--chip" />
          ))}
        </div>
        <div className="research-skeleton research-skeleton--block" />
        <div className="research-skeleton research-skeleton--line" />
        <div className="research-skeleton research-skeleton--block" />
      </div>
      {statusLabel ? (
        <span className="research-library__sr-only" role="status" aria-live="polite">
          {statusLabel}
        </span>
      ) : null}
    </div>
  );
}
