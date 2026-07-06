"use client";

import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import SectionCard from "@/components/ui/SectionCard";
import SectionHeader from "@/components/ui/SectionHeader";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  moduleSkeletonStatusKey,
  moduleStatusBadgeVariant,
  moduleStatusLabelKey,
  WORKSPACE_MODULES,
  type WorkspaceModule,
} from "@/lib/workspaceModules";
import { useWorkspaceLanguage } from "@/lib/useWorkspaceLanguage";

type ModuleSkeletonPageProps = {
  moduleId: string;
};

function findModule(moduleId: string): WorkspaceModule | undefined {
  return WORKSPACE_MODULES.find((item) => item.id === moduleId);
}

export default function ModuleSkeletonPage({ moduleId }: ModuleSkeletonPageProps) {
  const { language, setLanguage, tr } = useWorkspaceLanguage();
  const module = findModule(moduleId);

  if (!module) {
    return null;
  }

  const statusKey = moduleStatusLabelKey(module.status);
  const statusMessageKey = moduleSkeletonStatusKey(module.skeletonKind);

  return (
    <AppShell language={language} onLanguageChange={setLanguage}>
      <SectionCard>
        <SectionHeader title={tr(module.titleKey)} description={tr(module.pageDescKey)} />
        <div className="module-skeleton-meta">
          <StatusBadge
            label={tr(statusKey)}
            variant={moduleStatusBadgeVariant(module.status)}
          />
          <p className="section-meta">{tr(statusMessageKey)}</p>
          {module.skeletonKind === "migrating" && module.legacyAnchor ? (
            <p className="section-meta">
              {tr("legacyDemoHint")}{" "}
              <Link href={`/legacy#${module.legacyAnchor}`} className="module-card__link">
                {tr("openLegacyDemo")} →
              </Link>
            </p>
          ) : null}
        </div>
      </SectionCard>
    </AppShell>
  );
}

/** 供独立路由页面复用的薄包装 */
export function createModulePage(moduleId: string) {
  return function ModulePage() {
    return <ModuleSkeletonPage moduleId={moduleId} />;
  };
}
