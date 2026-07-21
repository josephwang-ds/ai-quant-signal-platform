"use client";

import { useEffect, useId, useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import type { CreateResearchInput } from "@/lib/researchRepository";

export type NewResearchModalLabels = {
  title: string;
  localNote: string;
  name: string;
  question: string;
  hypothesis: string;
  tags: string;
  tagsHint: string;
  create: string;
  cancel: string;
  errorName: string;
  errorQuestion: string;
  errorHypothesis: string;
};

export type NewResearchModalProps = {
  open: boolean;
  labels: NewResearchModalLabels;
  busy?: boolean;
  onClose: () => void;
  onCreate: (input: CreateResearchInput) => void | Promise<void>;
};

function makeDefaultForm() {
  return {
    name: "",
    researchQuestion: "",
    hypothesis: "",
    tags: "",
  };
}

/** Create a research question — experiments are designed inside the research later. */
export default function NewResearchModal({
  open,
  labels,
  busy = false,
  onClose,
  onCreate,
}: NewResearchModalProps) {
  const titleId = useId();
  const descriptionId = useId();
  const [form, setForm] = useState(makeDefaultForm);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [busy, onClose, open]);

  if (!open) return null;

  function updateField<K extends keyof ReturnType<typeof makeDefaultForm>>(
    key: K,
    value: ReturnType<typeof makeDefaultForm>[K]
  ) {
    setForm((previous) => ({ ...previous, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!form.name.trim()) return setError(labels.errorName);
    if (!form.researchQuestion.trim()) return setError(labels.errorQuestion);
    if (!form.hypothesis.trim()) return setError(labels.errorHypothesis);

    setError(null);
    await onCreate({
      name: form.name.trim(),
      researchQuestion: form.researchQuestion.trim(),
      hypothesis: form.hypothesis.trim(),
      tags: form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
    });
    setForm(makeDefaultForm());
  }

  return (
    <div
      className="research-modal"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <div
        className="research-modal__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
      >
        <header className="research-modal__header">
          <div>
            <h2 id={titleId} className="research-modal__title">
              {labels.title}
            </h2>
            <p id={descriptionId} className="section-meta">
              {labels.localNote}
            </p>
          </div>
        </header>

        <form className="research-modal__form" onSubmit={(event) => void handleSubmit(event)}>
          <div className="form-field">
            <label className="form-label" htmlFor="new-research-name">
              {labels.name} *
            </label>
            <input
              id="new-research-name"
              className="form-input"
              value={form.name}
              onChange={(event) => updateField("name", event.target.value)}
              required
              autoFocus
              disabled={busy}
            />
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="new-research-question">
              {labels.question} *
            </label>
            <textarea
              id="new-research-question"
              className="form-textarea"
              rows={3}
              value={form.researchQuestion}
              onChange={(event) => updateField("researchQuestion", event.target.value)}
              required
              disabled={busy}
            />
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="new-research-hypothesis">
              {labels.hypothesis} *
            </label>
            <textarea
              id="new-research-hypothesis"
              className="form-textarea"
              rows={3}
              value={form.hypothesis}
              onChange={(event) => updateField("hypothesis", event.target.value)}
              required
              disabled={busy}
            />
          </div>

          <div className="form-field">
            <label className="form-label" htmlFor="new-research-tags">
              {labels.tags}
            </label>
            <input
              id="new-research-tags"
              className="form-input"
              value={form.tags}
              placeholder={labels.tagsHint}
              onChange={(event) => updateField("tags", event.target.value)}
              disabled={busy}
            />
          </div>

          {error ? <p className="research-modal__error" role="alert">{error}</p> : null}

          <footer className="research-modal__actions">
            <Button type="button" className="btn--ghost" onClick={onClose} disabled={busy}>
              {labels.cancel}
            </Button>
            <Button type="submit" primary disabled={busy}>
              {labels.create}
            </Button>
          </footer>
        </form>
      </div>
    </div>
  );
}
