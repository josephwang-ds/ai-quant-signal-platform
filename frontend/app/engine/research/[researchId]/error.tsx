"use client";

import Link from "next/link";
import { useEffect } from "react";
import Button from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import SectionCard from "@/components/ui/SectionCard";

type ActiveResearchDetailErrorProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

/**
 * Active-research route error UI stays local-catalog specific and hides digests.
 */
export default function ActiveResearchDetailError({
  error,
  reset,
}: ActiveResearchDetailErrorProps) {
  useEffect(() => {
    console.error("Active research route error", error.name, error.message);
  }, [error]);

  return (
    <main className="route-error-shell">
      <SectionCard error>
        <ErrorAlert
          title="The Research Workspace could not be loaded."
          message="A temporary rendering problem occurred. Retry the page, or return to the research list. No invented metrics are shown."
        />
        <div className="button-row route-error-shell__actions">
          <Button primary onClick={() => reset()}>
            Retry
          </Button>
          <Link href="/" className="btn btn--ghost">
            Back to Research List
          </Link>
        </div>
      </SectionCard>
    </main>
  );
}
