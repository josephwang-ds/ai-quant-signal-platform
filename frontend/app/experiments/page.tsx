import { Suspense } from "react";
import ExperimentsPage from "@/components/features/experiments/ExperimentsPage";
import LoadingState from "@/components/ui/LoadingState";

export default function Page() {
  return (
    <Suspense fallback={<LoadingState message="Loading..." />}>
      <ExperimentsPage />
    </Suspense>
  );
}
