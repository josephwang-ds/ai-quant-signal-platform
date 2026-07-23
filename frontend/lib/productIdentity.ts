import type { Metadata } from "next";

/** Shared product identity for browser chrome and Open Graph. */
export const PRODUCT_NAME = "AI Quant Research Workspace";
export const PRODUCT_VERSION = "0.1.0";
export const PRODUCT_REPO_URL =
  "https://github.com/josephwang-ds/ai-quant-signal-platform";
export const PRODUCT_COPYRIGHT = "© 2026 Joseph Wang";

export const rootMetadata: Metadata = {
  title: {
    default: PRODUCT_NAME,
    template: `%s · ${PRODUCT_NAME}`,
  },
  description:
    "A governed quantitative research workspace for turning hypotheses into reproducible evidence, robustness review, and controlled decisions.",
  applicationName: PRODUCT_NAME,
  openGraph: {
    title: PRODUCT_NAME,
    description:
      "Move quantitative hypotheses through experiments, validation, robustness review, and controlled decisions.",
    type: "website",
    siteName: PRODUCT_NAME,
  },
  twitter: {
    card: "summary",
    title: PRODUCT_NAME,
    description:
      "A research operating system for reproducible quantitative evidence. Portfolio demonstration only.",
  },
};
