import { render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  resetBackendReadinessForTests,
  warmBackend,
} from "@/lib/apiRequest";
import { useBackendRecovery } from "@/lib/useBackendRecovery";

function Harness({
  status,
  recover,
}: {
  status: string;
  recover: () => void;
}) {
  useBackendRecovery(status, recover);
  return null;
}

describe("useBackendRecovery", () => {
  afterEach(() => {
    resetBackendReadinessForTests();
    vi.unstubAllGlobals();
  });

  it("retries an errored panel after the shared backend becomes ready", async () => {
    const recover = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "ai-quant-signal-backend",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    render(<Harness status="error" recover={recover} />);
    await warmBackend({ force: true });

    await waitFor(() => expect(recover).toHaveBeenCalledTimes(1));
  });

  it("does not duplicate a request that is still loading", async () => {
    const recover = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "ok",
            service: "ai-quant-signal-backend",
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    render(<Harness status="loading" recover={recover} />);
    await warmBackend({ force: true });

    expect(recover).not.toHaveBeenCalled();
  });
});
