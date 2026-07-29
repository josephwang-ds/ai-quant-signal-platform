import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import SectionCard from "@/components/ui/SectionCard";

/** Honest route-level loading skeleton for the active research workspace. */
export default function ActiveResearchDetailLoading() {
  return (
    <SectionCard>
      <ResearchWorkspaceSkeleton />
    </SectionCard>
  );
}
