"use client";

import { useState } from "react";
import Button from "@/components/ui/Button";
import type { Language } from "@/lib/i18n";
import type { SnapshotFinding } from "@/lib/intelligence/types";

export type FindingListProps = {
  findings: SnapshotFinding[];
  language: Language;
  initialVisible?: number;
};

export default function FindingList({
  findings,
  language,
  initialVisible = 5,
}: FindingListProps) {
  const zh = language === "zh";
  const [expanded, setExpanded] = useState(false);
  const needsDisclosure = findings.length > initialVisible;
  const visible =
    expanded || !needsDisclosure
      ? findings
      : findings.slice(0, initialVisible);

  if (findings.length === 0) {
    return (
      <p className="published-workspace__muted" role="status">
        {zh
          ? "此摘要未发布关键发现。"
          : "No key findings were published in this summary."}
      </p>
    );
  }

  return (
    <div data-testid="finding-list">
      <ol className="published-workspace__finding-list">
        {visible.map((finding, index) => (
          <li key={`${finding.code ?? "finding"}-${index}`}>
            <p className="published-workspace__finding-statement">
              {finding.statement}
            </p>
            {finding.code || finding.category ? (
              <p className="published-workspace__finding-meta">
                {[finding.code, finding.category].filter(Boolean).join(" · ")}
              </p>
            ) : null}
          </li>
        ))}
      </ol>
      {needsDisclosure ? (
        <Button
          onClick={() => setExpanded((value) => !value)}
          data-testid="finding-list-toggle"
          aria-expanded={expanded}
        >
          {expanded
            ? zh
              ? "收起"
              : "Show fewer"
            : zh
              ? `显示全部（${findings.length}）`
              : `Show all (${findings.length})`}
        </Button>
      ) : null}
    </div>
  );
}
