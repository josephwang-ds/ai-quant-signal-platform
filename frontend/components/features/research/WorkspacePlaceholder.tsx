import EmptyState from "@/components/ui/EmptyState";
import ResearchCenterHeader from "@/components/features/research/ux/ResearchCenterHeader";
import ResearchBand from "@/components/features/research/ux/ResearchBand";

type WorkspacePlaceholderProps = {
  title: string;
  summary: string;
  plannedCapabilities: string[];
  deferredNote?: string;
  emptyTitle?: string;
  capabilitiesCaption?: string;
};

/**
 * Informational placeholder for deferred lifecycle sections (e.g. Archive).
 * Uses shared center header + empty-state patterns — no blank grey boxes.
 */
export default function WorkspacePlaceholder({
  title,
  summary,
  plannedCapabilities,
  deferredNote = "Deferred to a later PR. No workflows are executable in this mock.",
  emptyTitle = "Not available yet",
  capabilitiesCaption = "Planned capabilities",
}: WorkspacePlaceholderProps) {
  return (
    <section className="research-center" aria-label={title}>
      <ResearchCenterHeader title={title} description={summary} />
      <ResearchBand caption={capabilitiesCaption} glyph="progress">
        <ul className="research-plain-list">
          {plannedCapabilities.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </ResearchBand>
      <hr className="overview-divider" />
      <EmptyState title={emptyTitle} description={deferredNote} />
    </section>
  );
}
