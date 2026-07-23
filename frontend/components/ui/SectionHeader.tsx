type SectionHeaderProps = {
  title: string;
  description?: string;
  level?: 1 | 2 | 3;
};

export default function SectionHeader({
  title,
  description,
  level = 2,
}: SectionHeaderProps) {
  const Heading = level === 1 ? "h1" : level === 3 ? "h3" : "h2";

  return (
    <div className="section-header">
      <Heading className="section-header__title">{title}</Heading>
      {description ? <p className="section-header__description">{description}</p> : null}
    </div>
  );
}
