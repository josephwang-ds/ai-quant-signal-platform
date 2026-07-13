import { Suspense } from "react";
import ResearchWorkspacePage from "@/components/features/research/ResearchWorkspacePage";
import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import AppShell from "@/components/layout/AppShell";
import SectionCard from "@/components/ui/SectionCard";

type ResearchDetailRouteProps = {
  params: Promise<{ researchId: string }>;
};

function DetailFallback() {
  return (
    <AppShell language="en" onLanguageChange={() => undefined}>
      <SectionCard>
        <ResearchWorkspaceSkeleton />
      </SectionCard>
    </AppShell>
  );
}

/** /research/[researchId] — Research Workspace Detail（PR-003）。 */
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
