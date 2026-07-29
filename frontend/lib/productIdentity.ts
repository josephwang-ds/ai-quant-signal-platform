import type { Metadata } from "next";

/**
 * Canonical product identity — keep README, GitHub, site chrome, and resume copy aligned.
 *
 * Slogan:
 *   AI Investment Intelligence Platform
 *   Built on an Evidence-driven Quant Research Engine.
 *
 * Philosophy:
 *   Every AI insight is backed by structured research evidence.
 *   Explainable. Traceable. Reviewable.
 */

export const PRODUCT_NAME = "AI Investment Intelligence Platform";
export const PRODUCT_NAME_ZH = "AI 投资智能平台";

export const PRODUCT_TAGLINE =
  "Built on an Evidence-driven Quant Research Engine.";
export const PRODUCT_TAGLINE_ZH = "建立在证据驱动的量化研究引擎之上。";

export const PRODUCT_PHILOSOPHY =
  "Every AI insight is backed by structured research evidence. Explainable. Traceable. Reviewable.";
export const PRODUCT_PHILOSOPHY_ZH =
  "每一条 AI 洞察都有结构化研究证据支撑。可解释。可追溯。可审阅。";

/** One-line blurb for metadata / Open Graph (English). */
export const PRODUCT_BLURB = `${PRODUCT_TAGLINE} ${PRODUCT_PHILOSOPHY}`;

export const PRODUCT_VERSION = "0.1.0";
export const PRODUCT_REPO_URL =
  "https://github.com/josephwang-ds/ai-quant-signal-platform";
export const PRODUCT_COPYRIGHT = "© 2026 Joseph Wang";

export const rootMetadata: Metadata = {
  title: {
    default: PRODUCT_NAME,
    template: `%s · ${PRODUCT_NAME}`,
  },
  description: PRODUCT_BLURB,
  applicationName: PRODUCT_NAME,
  openGraph: {
    title: PRODUCT_NAME,
    description: PRODUCT_BLURB,
    type: "website",
    siteName: PRODUCT_NAME,
  },
  twitter: {
    card: "summary",
    title: PRODUCT_NAME,
    description: PRODUCT_BLURB,
  },
};
