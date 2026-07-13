import type { NotebookEntryType } from "@/types/notebook";

type NotebookEntryTypeBadgeProps = {
  entryType: NotebookEntryType;
};

const TYPE_CLASS: Record<NotebookEntryType, string> = {
  Observation: "notebook-type-badge--observation",
  Hypothesis: "notebook-type-badge--hypothesis",
  Decision: "notebook-type-badge--decision",
  Action: "notebook-type-badge--action",
  Result: "notebook-type-badge--result",
  Reflection: "notebook-type-badge--reflection",
};

/** 条目类型徽标：克制色调，非社交 feed 风格。 */
export default function NotebookEntryTypeBadge({
  entryType,
}: NotebookEntryTypeBadgeProps) {
  return (
    <span className={`notebook-type-badge ${TYPE_CLASS[entryType]}`}>
      {entryType}
    </span>
  );
}
