type EvidenceReferenceListProps = {
  refs: string[];
  title: string;
  empty: string;
};

export default function EvidenceReferenceList({
  refs,
  title,
  empty,
}: EvidenceReferenceListProps) {
  return (
    <section className="validation-evidence" aria-label={title}>
      <h4 className="validation-evidence__title">{title}</h4>
      {refs.length === 0 ? (
        <p className="validation-evidence__empty">{empty}</p>
      ) : (
        <ul className="validation-evidence__list">
          {refs.map((ref) => (
            <li key={ref} className="font-mono">
              {ref}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
