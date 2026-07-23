"use client";

import { useEffect, useId } from "react";
import Button from "@/components/ui/Button";

type DeleteResearchModalProps = {
  open: boolean;
  researchName: string;
  busy?: boolean;
  labels: {
    title: string;
    description: string;
    irreversible: string;
    confirm: string;
    cancel: string;
    deleting: string;
  };
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
};

export default function DeleteResearchModal({
  open,
  researchName,
  busy = false,
  labels,
  onClose,
  onConfirm,
}: DeleteResearchModalProps) {
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!open) return;
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !busy) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [busy, onClose, open]);

  if (!open) return null;

  return (
    <div
      className="research-modal"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !busy) onClose();
      }}
    >
      <div
        className="research-modal__panel research-modal__panel--compact"
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
              {labels.description.replace("{name}", researchName)}
            </p>
          </div>
        </header>
        <p className="research-modal__danger-note">{labels.irreversible}</p>
        <footer className="research-modal__actions">
          <Button onClick={onClose} disabled={busy}>
            {labels.cancel}
          </Button>
          <Button
            className="btn--danger"
            onClick={() => void onConfirm()}
            disabled={busy}
            autoFocus
          >
            {busy ? labels.deleting : labels.confirm}
          </Button>
        </footer>
      </div>
    </div>
  );
}
