"use client";

import type { Language } from "@/lib/i18n";
import type { SnapshotLimitation } from "@/lib/intelligence/types";

export type LimitationListProps = {
  limitations: SnapshotLimitation[];
  language: Language;
};

export default function LimitationList({
  limitations,
  language,
}: LimitationListProps) {
  const zh = language === "zh";

  if (limitations.length === 0) {
    return (
      <p className="published-workspace__muted" role="status">
        {zh
          ? "此摘要未记录限制说明。"
          : "No limitations were recorded in this summary."}
      </p>
    );
  }

  return (
    <ul className="published-workspace__limitation-list" data-testid="limitation-list">
      {limitations.map((limitation, index) => (
        <li key={`${limitation.code ?? "limitation"}-${index}`}>
          <p className="published-workspace__limitation-statement">
            {limitation.statement}
          </p>
          {limitation.code ? (
            <p className="published-workspace__limitation-meta">{limitation.code}</p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
