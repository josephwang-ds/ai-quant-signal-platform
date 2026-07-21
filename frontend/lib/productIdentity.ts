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
    "A research workspace for quantitative experiments, validation, and governed decisions. Portfolio demonstration only — not investment advice and not live trading.",
  applicationName: PRODUCT_NAME,
  openGraph: {
    title: PRODUCT_NAME,
    description:
      "Research operating space for quantitative ideas: evidence, validation, and decisions. Demo only — not investment advice.",
    type: "website",
    siteName: PRODUCT_NAME,
  },
  twitter: {
    card: "summary",
    title: PRODUCT_NAME,
    description:
      "Research workspace for quantitative experiments and validation. Portfolio demonstration only.",
  },
};
