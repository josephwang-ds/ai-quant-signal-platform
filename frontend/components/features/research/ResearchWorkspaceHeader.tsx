"use client";

import Link from "next/link";
import { useId, useState } from "react";
import Button from "@/components/ui/Button";
import EvaluationPendingNotice from "@/components/features/research/EvaluationPendingNotice";
import StatusBadge, { researchLifecycleVariant } from "@/components/ui/StatusBadge";
import TagList from "@/components/ui/TagList";
import type { Language } from "@/lib/i18n";
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
};

export type ResearchWorkspaceHeaderProps = {
  research: ResearchDetail;
  language: Language;
  labels: ResearchWorkspaceHeaderLabels;
};

/** 单个研究工作区头部：身份、状态、建议与非破坏性更多操作。 */
export default function ResearchWorkspaceHeader({
  research,
  language,
  labels,
}: ResearchWorkspaceHeaderProps) {
  const menuId = useId();
  const [menuOpen, setMenuOpen] = useState(false);

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
            <div id={menuId} className="research-workspace-header__menu-panel" role="menu">
              <p className="section-meta">{labels.moreActionsHint}</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="research-workspace-header__title-row">
        <div>
          <h1 className="research-workspace-header__name">{research.name}</h1>
          <p className="research-workspace-header__question">{research.researchQuestion}</p>
          <p className="research-workspace-header__publicity">
            {research.integrity.publicityLabel}
          </p>
        </div>
        <div className="research-workspace-header__badges">
          <StatusBadge
            label={research.status}
            variant={researchLifecycleVariant(research.status)}
          />
          <EvaluationPendingNotice
            label={labels.confidence}
            message={research.integrity.evaluationPendingMessage}
          />
        </div>
      </div>

      <p className="research-workspace-header__explain">
        {research.integrity.explanatoryText}
      </p>

      <dl className="research-workspace-header__meta">
        <div>
          <dt>{labels.owner}</dt>
          <dd>{research.owner}</dd>
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

      <TagList tags={research.tags} label={labels.tags} />

      <p className="research-workspace-header__recommendation">
        <span className="research-workspace-header__recommendation-label">
          {labels.recommendation}
        </span>
        {research.currentRecommendation}
      </p>
    </header>
  );
}
