type InterpretationPanelProps = {
  title: string;
  sentences: string[];
  note: string;
};

export default function InterpretationPanel({
  title,
  sentences,
  note,
}: InterpretationPanelProps) {
  if (sentences.length === 0) {
    return null;
  }

  return (
    <div className="interpretation-panel">
      <h3 className="interpretation-panel__title">{title}</h3>
      <ul className="interpretation-panel__list">
        {sentences.map((sentence, index) => (
          <li key={index}>{sentence}</li>
        ))}
      </ul>
      <p className="interpretation-panel__note">{note}</p>
    </div>
  );
}
