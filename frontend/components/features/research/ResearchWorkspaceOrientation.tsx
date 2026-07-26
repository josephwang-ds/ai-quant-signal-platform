type ResearchWorkspaceOrientationProps = {
  nextMilestone: string;
  labels: {
    eyebrow: string;
    title: string;
    description: string;
    next: string;
  };
};

/**
 * A compact orientation layer for people entering a study workspace.
 * It explains the left-to-right workflow without duplicating research facts.
 */
export default function ResearchWorkspaceOrientation({
  nextMilestone,
  labels,
}: ResearchWorkspaceOrientationProps) {
  return (
    <section
      className="research-workspace-orientation"
      aria-labelledby="research-workspace-orientation-title"
    >
      <div className="research-workspace-orientation__copy">
        <p>{labels.eyebrow}</p>
        <h2 id="research-workspace-orientation-title">{labels.title}</h2>
        <span>{labels.description}</span>
      </div>
      <div className="research-workspace-orientation__next">
        <span>{labels.next}</span>
        <strong>{nextMilestone}</strong>
      </div>
    </section>
  );
}
