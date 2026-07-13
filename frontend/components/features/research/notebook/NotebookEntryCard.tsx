import TagList from "@/components/ui/TagList";
import type { Language } from "@/lib/i18n";
import { renderNotebookMarkdown } from "@/lib/notebookMarkdown";
import type { NotebookEntry } from "@/types/notebook";
import NotebookEntryTypeBadge from "./NotebookEntryTypeBadge";
import RelatedArtifactLink from "./RelatedArtifactLink";

function formatDateTime(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export type NotebookEntryCardLabels = {
  author: string;
  created: string;
  edited: string;
  related: string;
  tags: string;
};

type NotebookEntryCardProps = {
  entry: NotebookEntry;
  language: Language;
  labels: NotebookEntryCardLabels;
};

export default function NotebookEntryCard({
  entry,
  language,
  labels,
}: NotebookEntryCardProps) {
  return (
    <article className="notebook-entry-card" role="article">
      <header className="notebook-entry-card__header">
        <NotebookEntryTypeBadge entryType={entry.entryType} />
        <h3 className="notebook-entry-card__title">{entry.title}</h3>
      </header>

      <div
        className="notebook-entry-card__body notebook-markdown"
        dangerouslySetInnerHTML={{ __html: renderNotebookMarkdown(entry.body) }}
      />

      <footer className="notebook-entry-card__meta">
        <p className="notebook-entry-card__byline">
          <span>{labels.author}</span> {entry.author}
          <span className="notebook-entry-card__sep">·</span>
          <span>{labels.created}</span> {formatDateTime(entry.createdAt, language)}
          {entry.edited ? (
            <>
              <span className="notebook-entry-card__sep">·</span>
              <span className="notebook-entry-card__edited">{labels.edited}</span>
            </>
          ) : null}
        </p>

        {entry.relatedArtifact ? (
          <RelatedArtifactLink artifact={entry.relatedArtifact} label={labels.related} />
        ) : null}

        <TagList tags={entry.tags} label={labels.tags} className="notebook-entry-card__tags" />
      </footer>
    </article>
  );
}
