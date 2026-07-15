import { Suspense } from "react";
import ResearchWorkspacePage from "@/components/features/research/ResearchWorkspacePage";
import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import SectionCard from "@/components/ui/SectionCard";

type ResearchDetailRouteProps = {
  params: Promise<{ researchId: string }>;
};

/**
 * Suspense fallback for useSearchParams() in the client workspace.
 *
 * Must remain free of Client Component event-handler props. A previous
 * Server Component fallback passed a no-op language callback into the
 * shared shell and crashed production with digest 440809330
 * ("Event handlers cannot be passed to Client Component props").
 */
function DetailFallback() {
  return (
    <SectionCard>
      <ResearchWorkspaceSkeleton />
    </SectionCard>
  );
}

/** /research/[researchId] — Research Workspace Detail（PR-003 / PR-017）. */
export default async function ResearchDetailRoute({
  params,
}: ResearchDetailRouteProps) {
  const { researchId } = await params;

  return (
    <Suspense fallback={<DetailFallback />}>
      <ResearchWorkspacePage researchId={researchId} />
    </Suspense>
  );
}
