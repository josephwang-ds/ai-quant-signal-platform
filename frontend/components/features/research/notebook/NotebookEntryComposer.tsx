"use client";

import Button from "@/components/ui/Button";
import type { NotebookComposerValues, NotebookEntryType } from "@/types/notebook";
import { NOTEBOOK_ENTRY_TYPES } from "@/types/notebook";
import type { NotebookComposerErrors } from "@/lib/researchNotebook";

export type NotebookArtifactOption = {
  id: string;
  label: string;
};

export type NotebookEntryComposerLabels = {
  title: string;
  entryType: string;
  entryTitle: string;
  content: string;
  tags: string;
  tagsHint: string;
  relatedArtifact: string;
  relatedNone: string;
  save: string;
  cancel: string;
};

type NotebookEntryComposerProps = {
  open: boolean;
  values: NotebookComposerValues;
  errors: NotebookComposerErrors;
  artifactOptions: NotebookArtifactOption[];
  labels: NotebookEntryComposerLabels;
  onChange: (values: NotebookComposerValues) => void;
  onSave: () => void;
  onCancel: () => void;
};

/** 客户端条目编辑器（mock / local state only）。 */
export default function NotebookEntryComposer({
  open,
  values,
  errors,
  artifactOptions,
  labels,
  onChange,
  onSave,
  onCancel,
}: NotebookEntryComposerProps) {
  if (!open) {
    return null;
  }

  return (
    <section className="notebook-composer" aria-label={labels.title} role="region">
      <h3 className="notebook-composer__title">{labels.title}</h3>

      <div className="notebook-composer__grid">
        <div className="form-field">
          <label className="form-label" htmlFor="notebook-entry-type">
            {labels.entryType}
          </label>
          <select
            id="notebook-entry-type"
            className={`form-select${errors.entryType ? " is-invalid" : ""}`}
            value={values.entryType}
            onChange={(event) =>
              onChange({
                ...values,
                entryType: event.target.value as NotebookEntryType | "",
              })
            }
          >
            <option value="">—</option>
            {NOTEBOOK_ENTRY_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          {errors.entryType ? (
            <p className="form-error" role="alert">
              {errors.entryType}
            </p>
          ) : null}
        </div>

        <div className="form-field notebook-composer__title-field">
          <label className="form-label" htmlFor="notebook-entry-title">
            {labels.entryTitle}
          </label>
          <input
            id="notebook-entry-title"
            className={`form-input${errors.title ? " is-invalid" : ""}`}
            value={values.title}
            onChange={(event) =>
              onChange({ ...values, title: event.target.value })
            }
          />
          {errors.title ? (
            <p className="form-error" role="alert">
              {errors.title}
            </p>
          ) : null}
        </div>
      </div>

      <div className="form-field">
        <label className="form-label" htmlFor="notebook-entry-body">
          {labels.content}
        </label>
        <textarea
          id="notebook-entry-body"
          className={`form-input notebook-composer__textarea${
            errors.body ? " is-invalid" : ""
          }`}
          rows={8}
          value={values.body}
          onChange={(event) =>
            onChange({ ...values, body: event.target.value })
          }
          placeholder="Supports light Markdown: ## heading, **bold**, - list, `code`"
        />
        {errors.body ? (
          <p className="form-error" role="alert">
            {errors.body}
          </p>
        ) : null}
      </div>

      <div className="notebook-composer__grid">
        <div className="form-field">
          <label className="form-label" htmlFor="notebook-entry-tags">
            {labels.tags}
          </label>
          <input
            id="notebook-entry-tags"
            className="form-input"
            value={values.tags}
            onChange={(event) =>
              onChange({ ...values, tags: event.target.value })
            }
          />
          <p className="form-hint">{labels.tagsHint}</p>
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="notebook-entry-artifact">
            {labels.relatedArtifact}
          </label>
          <select
            id="notebook-entry-artifact"
            className="form-select"
            value={values.relatedArtifactId}
            onChange={(event) =>
              onChange({ ...values, relatedArtifactId: event.target.value })
            }
          >
            <option value="">{labels.relatedNone}</option>
            {artifactOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="notebook-composer__actions">
        <Button primary onClick={onSave}>
          {labels.save}
        </Button>
        <Button onClick={onCancel} className="btn--ghost">
          {labels.cancel}
        </Button>
      </div>
    </section>
  );
}
