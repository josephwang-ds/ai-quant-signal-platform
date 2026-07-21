type ResearchCenterHeaderProps = {
  title: string;
  description?: string;
  titleId?: string;
};

/**
 * Shared page header for lifecycle centers:
 * small title hierarchy + optional description.
 */
export default function ResearchCenterHeader({
  title,
  description,
  titleId,
}: ResearchCenterHeaderProps) {
  return (
    <header className="research-center__header">
      <h2 id={titleId} className="research-center__title">
        {title}
      </h2>
      {description ? (
        <p className="research-center__description">{description}</p>
      ) : null}
    </header>
  );
}
