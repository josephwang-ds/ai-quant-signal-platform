/** Research List 加载骨架，避免空白闪烁。 */
export default function ResearchListSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="research-list-grid" aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <div key={index} className="research-card research-card--skeleton">
          <div className="research-skeleton research-skeleton--title" />
          <div className="research-skeleton research-skeleton--line" />
          <div className="research-skeleton research-skeleton--line research-skeleton--short" />
          <div className="research-skeleton-meta">
            <div className="research-skeleton research-skeleton--chip" />
            <div className="research-skeleton research-skeleton--chip" />
            <div className="research-skeleton research-skeleton--chip" />
          </div>
          <div className="research-skeleton research-skeleton--block" />
        </div>
      ))}
    </div>
  );
}
