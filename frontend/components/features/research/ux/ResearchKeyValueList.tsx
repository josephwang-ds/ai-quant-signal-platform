import type { ReactNode } from "react";

export type ResearchKeyValueItem = {
  id: string;
  label: string;
  value: ReactNode;
};

export type ResearchKeyValueListProps = {
  items: ResearchKeyValueItem[];
};

/**
 * Shared key-value list for deployment / summary / metadata blocks.
 */
export default function ResearchKeyValueList({ items }: ResearchKeyValueListProps) {
  return (
    <dl className="research-kv">
      {items.map((item) => (
        <div key={item.id}>
          <dt>{item.label}</dt>
          <dd>{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
