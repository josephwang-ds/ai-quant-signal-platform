"use client";

import { useEffect, useId, useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import type { CreateResearchInput } from "@/lib/researchRepository";

export type NewResearchModalLabels = {
  title: string;
  localNote: string;
  name: string;
  question: string;
  symbol: string;
  startDate: string;
  endDate: string;
  shortWindow: string;
  longWindow: string;
  transactionCost: string;
  owner: string;
  tags: string;
  tagsHint: string;
  create: string;
  cancel: string;
  errorName: string;
  errorQuestion: string;
  errorSymbol: string;
  errorShortWindow: string;
  errorLongWindow: string;
  errorDateRange: string;
  errorTransactionCost: string;
};

export type NewResearchModalProps = {
  open: boolean;
  labels: NewResearchModalLabels;
  busy?: boolean;
  onClose: () => void;
  onCreate: (input: CreateResearchInput) => void | Promise<void>;
};

function defaultEndDate(): string {
  return new Date(Date.now() - 24 * 60 * 60 * 1000)
    .toISOString()
    .slice(0, 10);
}

function makeDefaultForm() {
  return {
    name: "",
    researchQuestion: "",
    symbol: "SPY",
    startDate: "2018-01-01",
    endDate: defaultEndDate(),
    shortWindow: "20",
    longWindow: "60",
    transactionCost: "0.001",
    owner: "Research Workspace",
    tags: "ma-crossover",
  };
}

/** Create one local MA Crossover definition; evidence remains backend-derived. */
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
    const shortWindow = Number(form.shortWindow);
    const longWindow = Number(form.longWindow);
    const transactionCost = Number(form.transactionCost || "0.001");

    if (!form.name.trim()) return setError(labels.errorName);
    if (!form.researchQuestion.trim()) return setError(labels.errorQuestion);
    if (!form.symbol.trim()) return setError(labels.errorSymbol);
    if (!Number.isInteger(shortWindow) || shortWindow <= 0) {
      return setError(labels.errorShortWindow);
    }
    if (!Number.isInteger(longWindow) || longWindow <= shortWindow) {
      return setError(labels.errorLongWindow);
    }
    if (!form.startDate || !form.endDate || form.startDate >= form.endDate) {
      return setError(labels.errorDateRange);
    }
    if (!Number.isFinite(transactionCost) || transactionCost < 0) {
      return setError(labels.errorTransactionCost);
    }

    setError(null);
    const symbol = form.symbol.trim().toUpperCase();
    await onCreate({
      name: form.name.trim(),
      researchQuestion: form.researchQuestion.trim(),
      symbol,
      benchmark: symbol,
      startDate: form.startDate,
      endDate: form.endDate,
      shortWindow,
      longWindow,
      transactionCost,
      tags: form.tags
        .split(",")
        .map((tag) => tag.trim())
        .filter(Boolean),
      owner: form.owner.trim(),
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
          <span className="status-badge status-badge--neutral">MA Crossover</span>
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

          <div className="research-modal__row research-modal__row--three">
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-symbol">
                {labels.symbol} *
              </label>
              <input
                id="new-research-symbol"
                className="form-input font-mono"
                value={form.symbol}
                onChange={(event) => updateField("symbol", event.target.value.toUpperCase())}
                required
                disabled={busy}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-start">
                {labels.startDate} *
              </label>
              <input
                id="new-research-start"
                className="form-input"
                type="date"
                value={form.startDate}
                onChange={(event) => updateField("startDate", event.target.value)}
                required
                disabled={busy}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-end">
                {labels.endDate} *
              </label>
              <input
                id="new-research-end"
                className="form-input"
                type="date"
                value={form.endDate}
                onChange={(event) => updateField("endDate", event.target.value)}
                required
                disabled={busy}
              />
            </div>
          </div>

          <div className="research-modal__row research-modal__row--three">
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-short-window">
                {labels.shortWindow} *
              </label>
              <input
                id="new-research-short-window"
                className="form-input font-mono"
                type="number"
                min="1"
                step="1"
                value={form.shortWindow}
                onChange={(event) => updateField("shortWindow", event.target.value)}
                required
                disabled={busy}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-long-window">
                {labels.longWindow} *
              </label>
              <input
                id="new-research-long-window"
                className="form-input font-mono"
                type="number"
                min="2"
                step="1"
                value={form.longWindow}
                onChange={(event) => updateField("longWindow", event.target.value)}
                required
                disabled={busy}
              />
            </div>
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-cost">
                {labels.transactionCost}
              </label>
              <input
                id="new-research-cost"
                className="form-input font-mono"
                type="number"
                min="0"
                step="0.0001"
                value={form.transactionCost}
                onChange={(event) => updateField("transactionCost", event.target.value)}
                disabled={busy}
              />
            </div>
          </div>

          <div className="research-modal__row">
            <div className="form-field">
              <label className="form-label" htmlFor="new-research-owner">
                {labels.owner}
              </label>
              <input
                id="new-research-owner"
                className="form-input"
                value={form.owner}
                onChange={(event) => updateField("owner", event.target.value)}
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
