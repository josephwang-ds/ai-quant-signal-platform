import type { TranslationKey } from "@/lib/i18n";

export type CoverageStatus = "active" | "basic";

export type AssetClassRow = {
  id: string;
  assetClassKey: TranslationKey;
  marketKey: TranslationKey;
  examples: string;
  sourceKey: TranslationKey;
  status: CoverageStatus;
  notesKey?: TranslationKey;
};

export type SymbolFormatRow = {
  id: string;
  labelKey: TranslationKey;
  example: string;
};

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
  {
    id: "crypto-yahoo",
    assetClassKey: "dcAssetCryptoYahoo",
    marketKey: "dcMarketCrypto",
    examples: "BTC-USD, ETH-USD, SOL-USD",
    sourceKey: "dcSourceYahoo",
    status: "basic",
    notesKey: "dcNoteCryptoLimitations",
  },
  {
    id: "indices",
    assetClassKey: "dcAssetIndices",
    marketKey: "dcMarketGlobal",
    examples: "^GSPC, ^IXIC, ^HSI",
    sourceKey: "dcSourceYahoo",
    status: "basic",
  },
  {
    id: "fx",
    assetClassKey: "dcAssetFx",
    marketKey: "dcMarketFx",
    examples: "EURUSD=X, JPY=X, CNH=X",
    sourceKey: "dcSourceYahoo",
    status: "basic",
  },
  {
    id: "futures",
    assetClassKey: "dcAssetFutures",
    marketKey: "dcMarketFutures",
    examples: "GC=F, CL=F, SI=F",
    sourceKey: "dcSourceYahoo",
    status: "basic",
  },
];

export const SYMBOL_FORMAT_ROWS: SymbolFormatRow[] = [
  { id: "us", labelKey: "dcSymbolUsStock", example: "AAPL" },
  { id: "etf", labelKey: "dcSymbolEtf", example: "SPY" },
  { id: "hk", labelKey: "dcSymbolHkStock", example: "0700.HK" },
  { id: "sh", labelKey: "dcSymbolCnShanghai", example: "600519.SH" },
  { id: "sz", labelKey: "dcSymbolCnShenzhen", example: "000001.SZ" },
  { id: "crypto", labelKey: "dcSymbolCrypto", example: "BTC-USD" },
  { id: "fx", labelKey: "dcSymbolFx", example: "EURUSD=X" },
  { id: "futures", labelKey: "dcSymbolFutures", example: "GC=F" },
];

export function coverageStatusLabelKey(status: CoverageStatus): TranslationKey {
  switch (status) {
    case "active":
      return "statusActive";
    case "basic":
      return "statusBasicSupport";
  }
}

export function coverageStatusBadgeVariant(
  status: CoverageStatus
): "success" | "info" | "neutral" {
  switch (status) {
    case "active":
      return "success";
    case "basic":
      return "info";
  }
}
