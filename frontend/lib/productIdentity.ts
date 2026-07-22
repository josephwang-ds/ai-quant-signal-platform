import type { Metadata } from "next";

/** Shared product identity for browser chrome and Open Graph. */
export const PRODUCT_NAME = "AI Investment Intelligence Platform";
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
    "AI-assisted investment intelligence: watchlists, strategy runs, model comparison, and risk review. Portfolio demonstration only — not investment advice and not live trading.",
  applicationName: PRODUCT_NAME,
  openGraph: {
    title: PRODUCT_NAME,
    description:
      "Explore investment ideas with evidence-backed comparison and risk review. Demo only — not investment advice.",
    type: "website",
    siteName: PRODUCT_NAME,
  },
  twitter: {
    card: "summary",
    title: PRODUCT_NAME,
    description:
      "AI investment intelligence for watchlists, strategy studio, and model comparison. Portfolio demonstration only.",
  },
};
