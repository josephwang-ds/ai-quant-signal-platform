/** Research Workspace Detail 加载骨架。 */
export default function ResearchWorkspaceSkeleton() {
  return (
    <div className="research-workspace-skeleton" aria-hidden="true">
      <div className="research-skeleton research-skeleton--title" />
      <div className="research-skeleton research-skeleton--line" />
      <div className="research-skeleton research-skeleton--line research-skeleton--short" />
      <div className="research-workspace-skeleton__nav">
        {Array.from({ length: 8 }, (_, index) => (
          <div key={index} className="research-skeleton research-skeleton--chip" />
        ))}
      </div>
      <div className="research-workspace-skeleton__body">
        <div className="research-skeleton research-skeleton--block" />
        <div className="research-skeleton research-skeleton--block" />
      </div>
    </div>
  );
}
