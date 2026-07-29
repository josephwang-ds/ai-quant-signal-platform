import type { TranslationKey } from "@/lib/i18n";

export type ResearchReadiness =
  | "full_cross_sectional"
  | "strategy_support"
  | "basic_research";

export type ResearchReadyRow = {
  id: string;
  assetClassKey: TranslationKey;
  readiness: ResearchReadiness;
  supportKey: TranslationKey;
  detailKey: TranslationKey;
};

export type PriceOnlyRow = {
  id: string;
  labelKey: TranslationKey;
  examples: string;
};

export type SymbolFormatRow = {
  id: string;
  labelKey: TranslationKey;
  example: string;
};

/** @deprecated Prefer RESEARCH_READY_ROWS for presentation. */
export type CoverageStatus = "active";

/** @deprecated Prefer RESEARCH_READY_ROWS / PRICE_ONLY_ROWS. */
export type AssetClassRow = {
  id: string;
  assetClassKey: TranslationKey;
  marketKey: TranslationKey;
  examples: string;
  sourceKey: TranslationKey;
  status: CoverageStatus;
  notesKey?: TranslationKey;
};

export const RESEARCH_READY_ROWS: ResearchReadyRow[] = [
  {
    id: "us-stocks",
    assetClassKey: "dcAssetUsStocks",
    readiness: "full_cross_sectional",
    supportKey: "dcReadyFullCs",
    detailKey: "dcReadyFullCsDetail",
  },
  {
    id: "etfs",
    assetClassKey: "dcAssetEtfs",
    readiness: "strategy_support",
    supportKey: "dcReadyStrategy",
    detailKey: "dcReadyStrategyDetail",
  },
  {
    id: "hk-stocks",
    assetClassKey: "dcAssetHkStocks",
    readiness: "basic_research",
    supportKey: "dcReadyBasic",
    detailKey: "dcReadyBasicDetail",
  },
  {
    id: "cn-akshare",
    assetClassKey: "dcAssetCnAkShare",
    readiness: "basic_research",
    supportKey: "dcReadyBasic",
    detailKey: "dcReadyBasicDetail",
  },
];

export const PRICE_ONLY_ROWS: PriceOnlyRow[] = [
  {
    id: "indexes-fx-crypto",
    labelKey: "dcPriceOnlyBundle",
    examples: "^GSPC · EURUSD=X · BTC-USD",
  },
];

/** Kept for probe/format guides — research-ready symbols only. */
export const ASSET_CLASS_ROWS: AssetClassRow[] = [
  {
    id: "us-stocks",
    assetClassKey: "dcAssetUsStocks",
    marketKey: "dcMarketUs",
    examples: "AAPL, MSFT, NVDA, TSLA",
    sourceKey: "dcSourceYahoo",
    status: "active",
  },
  {
    id: "etfs",
    assetClassKey: "dcAssetEtfs",
    marketKey: "dcMarketUs",
    examples: "SPY, QQQ, IWM",
    sourceKey: "dcSourceYahoo",
    status: "active",
  },
  {
    id: "hk-stocks",
    assetClassKey: "dcAssetHkStocks",
    marketKey: "dcMarketHk",
    examples: "0700.HK, 9988.HK, 3690.HK",
    sourceKey: "dcSourceYahoo",
    status: "active",
  },
  {
    id: "cn-akshare",
    assetClassKey: "dcAssetCnAkShare",
    marketKey: "dcMarketCn",
    examples: "000001.SZ, 600519.SH",
    sourceKey: "dcSourceAkShare",
    status: "active",
    notesKey: "dcNoteCnAkShare",
  },
];

export const SYMBOL_FORMAT_ROWS: SymbolFormatRow[] = [
  { id: "us", labelKey: "dcSymbolUsStock", example: "AAPL" },
  { id: "etf", labelKey: "dcSymbolEtf", example: "SPY" },
  { id: "hk", labelKey: "dcSymbolHkStock", example: "0700.HK" },
  { id: "sh", labelKey: "dcSymbolCnShanghai", example: "600519.SH" },
  { id: "sz", labelKey: "dcSymbolCnShenzhen", example: "000001.SZ" },
];

export function coverageStatusLabelKey(status: CoverageStatus): TranslationKey {
  switch (status) {
    case "active":
      return "statusActive";
  }
}

export function coverageStatusBadgeVariant(
  status: CoverageStatus
): "success" | "info" | "neutral" {
  switch (status) {
    case "active":
      return "success";
  }
}
