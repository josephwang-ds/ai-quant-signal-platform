import { Suspense } from "react";
import PublishedResearchWorkspace from "@/components/features/intelligence-workspace/PublishedResearchWorkspace";
import PublishedWorkspaceSkeleton from "@/components/features/intelligence-workspace/PublishedWorkspaceSkeleton";
import { redirect } from "next/navigation";

type ResearchDetailRouteProps = {
  params: Promise<{ researchId: string }>;
};

/**
 * Temporary migration dispatcher:
 * - `run_*` → published intelligence workspace (Phase 4.6C1).
 * - legacy catalog ids → `/engine/research/[researchId]`.
 */
export default async function ResearchDetailRoute({
  params,
}: ResearchDetailRouteProps) {
  const { researchId } = await params;

  if (!researchId.startsWith("run_")) {
    redirect(`/engine/research/${encodeURIComponent(researchId)}`);
  }

  return (
    <Suspense
      fallback={
        <PublishedWorkspaceSkeleton
          testId="published-workspace-route-fallback"
          statusLabel="Loading published research workspace…"
        />
      }
    >
      <PublishedResearchWorkspace runId={researchId} />
    </Suspense>
  );
}
