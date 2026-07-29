import PublishedWorkspaceSkeleton from "@/components/features/intelligence-workspace/PublishedWorkspaceSkeleton";

/** Route-level loading — matches published workspace gate skeleton (not legacy Active Workspace). */
export default function ResearchDetailLoading() {
  return (
    <PublishedWorkspaceSkeleton statusLabel="Loading published research workspace…" />
  );
}
