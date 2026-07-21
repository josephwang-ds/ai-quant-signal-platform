import Link from "next/link";
import ResearchGlyph from "@/components/features/research/ResearchGlyph";

export type GuidedEntryItem = {
  id: string;
  href: string;
  label: string;
  description: string;
};

export type GuidedEntryPanelProps = {
  title: string;
  items: GuidedEntryItem[];
};

/**
 * Lightweight first-visit entry paths — panel, not a modal or tutorial.
 */
export default function GuidedEntryPanel({ title, items }: GuidedEntryPanelProps) {
  return (
    <section className="guided-entry" aria-label={title}>
      <p className="overview-caption">
        <ResearchGlyph name="workflow" />
        <span>{title}</span>
      </p>
      <ul className="guided-entry__list">
        {items.map((item) => (
          <li key={item.id}>
            <Link href={item.href} className="guided-entry__item">
              <span className="guided-entry__label">{item.label}</span>
              <span className="guided-entry__description">{item.description}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
