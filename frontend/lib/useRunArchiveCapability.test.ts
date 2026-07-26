import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useRunArchiveCapability } from "@/lib/useRunArchiveCapability";

const getDatabaseStatus = vi.fn();

vi.mock("@/lib/api", () => ({
  getDatabaseStatus: (...args: unknown[]) => getDatabaseStatus(...args),
}));

describe("useRunArchiveCapability", () => {
  beforeEach(() => {
    getDatabaseStatus.mockReset();
  });

  it("reports not-configured when database is unset", async () => {
    getDatabaseStatus.mockResolvedValue({
      configured: false,
      connected: false,
      message: "Database is not configured.",
      database: "supabase_postgres",
    });

    const { result } = renderHook(() => useRunArchiveCapability());

    await waitFor(() => {
      expect(result.current.availability).toBe("not-configured");
    });
    expect(result.current.canSave).toBe(false);
  });

  it("reports available when database is connected", async () => {
    getDatabaseStatus.mockResolvedValue({
      configured: true,
      connected: true,
      message: "Database connection successful.",
      database: "supabase_postgres",
    });

    const { result } = renderHook(() => useRunArchiveCapability());

    await waitFor(() => {
      expect(result.current.availability).toBe("available");
    });
    expect(result.current.canSave).toBe(true);
  });

  it("reports unavailable when configured but offline", async () => {
    getDatabaseStatus.mockResolvedValue({
      configured: true,
      connected: false,
      message: "Database connection failed.",
      database: "supabase_postgres",
    });

    const { result } = renderHook(() => useRunArchiveCapability());

    await waitFor(() => {
      expect(result.current.availability).toBe("unavailable");
    });
    expect(result.current.canSave).toBe(false);
  });

  it("can refresh after an offline failure", async () => {
    getDatabaseStatus
      .mockResolvedValueOnce({
        configured: true,
        connected: false,
        message: "Database connection failed.",
        database: "supabase_postgres",
      })
      .mockResolvedValueOnce({
        configured: true,
        connected: true,
        message: "Database connection successful.",
        database: "supabase_postgres",
      });

    const { result } = renderHook(() => useRunArchiveCapability());
    await waitFor(() => {
      expect(result.current.availability).toBe("unavailable");
    });

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.availability).toBe("available");
    expect(result.current.canSave).toBe(true);
  });
});
