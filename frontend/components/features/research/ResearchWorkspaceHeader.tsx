"use client";

import Link from "next/link";
import { useId, useState } from "react";
import Button from "@/components/ui/Button";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import type { Language } from "@/lib/i18n";
import {
  buildResearchProtocolParts,
  formatResearchProtocolLine,
} from "@/lib/researchProtocol";
import {
  benchmarkLabel,
  ownerLabel,
  researchNameLabel,
  researchQuestionLabel,
  researchStatusLabel,
} from "@/lib/researchDisplay";
import type { ResearchDetail } from "@/types/research";

function formatDate(value: string, language: Language): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(language === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export type ResearchWorkspaceHeaderLabels = {
  back: string;
  moreActions: string;
  moreActionsHint: string;
  owner: string;
  created: string;
  updated: string;
  recommendation: string;
  confidence: string;
  tags: string;
  benchmark: string;
};

export type ResearchWorkspaceHeaderProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchWorkspaceHeaderLabels;
};

/** Research Workspace hero — identity and lifecycle, not metric dump. */
export default function ResearchWorkspaceHeader({
  research,
  language,
  labels,
}: ResearchWorkspaceHeaderProps) {
  const menuId = useId();
  const [menuOpen, setMenuOpen] = useState(false);

  const protocol = formatResearchProtocolLine(
    buildResearchProtocolParts(research, null, language),
    language
  );

  return (
    <header className="research-workspace-header">
      <div className="research-workspace-header__top">
        <Link href="/" className="research-workspace-header__back">
          ← {labels.back}
        </Link>
        <div className="research-workspace-header__menu">
          <Button
            className="btn--ghost"
            aria-expanded={menuOpen}
            aria-controls={menuId}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {labels.moreActions}
          </Button>
          {menuOpen ? (
            <div
              id={menuId}
              className="research-workspace-header__menu-panel"
              role="menu"
            >
              <p className="section-meta">{labels.moreActionsHint}</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="research-workspace-header__title-row">
        <div>
          <h1 className="research-workspace-header__name">
            {researchNameLabel(research.id, research.name, language)}
          </h1>
          <p className="research-workspace-header__question">
            {researchQuestionLabel(research.id, research.researchQuestion, language)}
          </p>
          {protocol ? (
            <p className="research-workspace-header__protocol">{protocol}</p>
          ) : null}
        </div>
        <StatusBadge
          label={researchStatusLabel(research.status, language)}
          variant={researchLifecycleVariant(research.status)}
        />
      </div>

      <dl className="research-workspace-header__meta">
        <div>
          <dt>{labels.owner}</dt>
          <dd>{ownerLabel(research.owner, language)}</dd>
        </div>
        <div>
          <dt>{labels.benchmark}</dt>
          <dd>{benchmarkLabel(research.configuration.benchmark, language)}</dd>
        </div>
        <div>
          <dt>{labels.created}</dt>
          <dd>{formatDate(research.createdAt, language)}</dd>
        </div>
        <div>
          <dt>{labels.updated}</dt>
          <dd>{formatDate(research.updatedAt, language)}</dd>
        </div>
      </dl>
    </header>
  );
}
