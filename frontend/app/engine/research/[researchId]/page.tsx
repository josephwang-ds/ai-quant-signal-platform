import { Suspense } from "react";
import ResearchWorkspacePage from "@/components/features/research/ResearchWorkspacePage";
import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import SectionCard from "@/components/ui/SectionCard";

type ActiveResearchDetailRouteProps = {
  params: Promise<{ researchId: string }>;
};

function DetailFallback() {
  return (
    <SectionCard>
      <ResearchWorkspaceSkeleton />
    </SectionCard>
  );
}

/** Canonical active-research workspace route backed by the local catalog workflow. */
export default async function ActiveResearchDetailRoute({
  params,
}: ActiveResearchDetailRouteProps) {
  const { researchId } = await params;

  return (
    <Suspense fallback={<DetailFallback />}>
      <ResearchWorkspacePage researchId={researchId} />
    </Suspense>
  );
}
