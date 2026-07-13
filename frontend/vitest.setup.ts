import React from "react";
import { vi } from "vitest";
import "@testing-library/jest-dom/vitest";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    className?: string;
    "aria-current"?: string;
  }) => React.createElement("a", { href, ...props }, children),
}));
