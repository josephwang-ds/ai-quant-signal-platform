import ResearchWorkspaceSkeleton from "@/components/features/research/ResearchWorkspaceSkeleton";
import SectionCard from "@/components/ui/SectionCard";

/** Honest route-level loading skeleton — no fabricated metrics. */
export default function ResearchDetailLoading() {
  return (
    <SectionCard>
      <ResearchWorkspaceSkeleton />
    </SectionCard>
  );
}
