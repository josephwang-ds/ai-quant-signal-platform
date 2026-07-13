type WorkspacePlaceholderProps = {
  title: string;
  summary: string;
  plannedCapabilities: string[];
  deferredNote?: string;
};

/**
 * 非 Overview 分区的信息性占位：说明后续切片会交付什么。
 * 禁止空白灰盒与 lorem ipsum。
 */
export default function WorkspacePlaceholder({
  title,
  summary,
  plannedCapabilities,
  deferredNote = "Deferred to a later PR. No workflows are executable in this mock.",
}: WorkspacePlaceholderProps) {
  return (
    <section className="workspace-placeholder" aria-label={title}>
      <h2 className="workspace-placeholder__title">{title}</h2>
      <p className="workspace-placeholder__summary">{summary}</p>
      <h3 className="workspace-placeholder__subtitle">Planned capabilities</h3>
      <ul className="workspace-placeholder__list">
        {plannedCapabilities.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p className="workspace-placeholder__note">{deferredNote}</p>
    </section>
  );
}
