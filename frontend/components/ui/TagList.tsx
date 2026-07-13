type TagListProps = {
  tags: string[];
  label?: string;
  className?: string;
};

/** 研究标签列表（列表卡片与工作区头部复用）。 */
export default function TagList({
  tags,
  label = "Tags",
  className = "",
}: TagListProps) {
  if (tags.length === 0) {
    return null;
  }

  return (
    <ul
      className={`tag-list${className ? ` ${className}` : ""}`}
      aria-label={label}
    >
      {tags.map((tag) => (
        <li key={tag} className="tag-list__item">
          {tag}
        </li>
      ))}
    </ul>
  );
}
