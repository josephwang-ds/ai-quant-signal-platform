"use client";

import type { Language } from "@/lib/i18n";

export type IntegrityHintKind = "consumer_contract" | "opaque_evidence" | "integrity_recorded";

export type IntegrityHintProps = {
  kind: IntegrityHintKind;
  language: Language;
};

const LABELS: Record<IntegrityHintKind, { en: string; zh: string }> = {
  consumer_contract: { en: "Consumer contract", zh: "消费端契约" },
  opaque_evidence: { en: "Opaque evidence", zh: "不透明证据" },
  integrity_recorded: { en: "Integrity recorded", zh: "完整性已记录" },
};

export default function IntegrityHint({ kind, language }: IntegrityHintProps) {
  return (
    <span
      className={`published-workspace__integrity published-workspace__integrity--${kind}`}
      role="note"
    >
      {LABELS[kind][language]}
    </span>
  );
}
