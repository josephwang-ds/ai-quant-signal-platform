import type { TranslationKey } from "@/lib/i18n";

export type QuantTipDefinition = {
  id: string;
  titleKey: TranslationKey;
  bodyKey: TranslationKey;
  paths?: string[];
};

/** 量化研究小妙招：按路径优先匹配，否则按日期轮换 */
export const QUANT_TIPS: QuantTipDefinition[] = [
  {
    id: "fix-sample",
    titleKey: "quantTipFixSampleTitle",
    bodyKey: "quantTipFixSampleBody",
    paths: ["/strategy-lab", "/comparison", "/robustness"],
  },
  {
    id: "save-notes",
    titleKey: "quantTipSaveNotesTitle",
    bodyKey: "quantTipSaveNotesBody",
    paths: ["/strategy-lab", "/experiments"],
  },
  {
    id: "drawdown",
    titleKey: "quantTipDrawdownTitle",
    bodyKey: "quantTipDrawdownBody",
    paths: ["/strategy-lab", "/experiments", "/comparison"],
  },
  {
    id: "benchmark",
    titleKey: "quantTipBenchmarkTitle",
    bodyKey: "quantTipBenchmarkBody",
    paths: ["/comparison", "/strategy-lab"],
  },
  {
    id: "oos",
    titleKey: "quantTipOosTitle",
    bodyKey: "quantTipOosBody",
    paths: ["/robustness"],
  },
  {
    id: "filter-sort",
    titleKey: "quantTipFilterTitle",
    bodyKey: "quantTipFilterBody",
    paths: ["/experiments"],
  },
  {
    id: "signals",
    titleKey: "quantTipSignalsTitle",
    bodyKey: "quantTipSignalsBody",
    paths: ["/market-watch"],
  },
  {
    id: "general",
    titleKey: "quantTipGeneralTitle",
    bodyKey: "quantTipGeneralBody",
  },
];

export function pickQuantTip(pathname: string): QuantTipDefinition {
  const pathMatches = QUANT_TIPS.filter(
    (tip) => tip.paths?.some((prefix) => pathname.startsWith(prefix)) ?? false
  );
  const pool = pathMatches.length > 0 ? pathMatches : QUANT_TIPS;
  const dayIndex = Math.floor(Date.now() / 86_400_000);
  return pool[dayIndex % pool.length];
}
