import type { TranslationKey } from "@/lib/i18n";

export type CoverageStatus = "active" | "basic" | "planned" | "comingLater";

export type AssetClassRow = {
  id: string;
  assetClassKey: TranslationKey;
  marketKey: TranslationKey;
  examples: string;
  sourceKey: TranslationKey;
  status: CoverageStatus;
  notesKey?: TranslationKey;
};

export type PlannedProviderCard = {
  id: string;
  titleKey: TranslationKey;
  descKey: TranslationKey;
  status: CoverageStatus;
};

export type SymbolFormatRow = {
  id: string;
  labelKey: TranslationKey;
  example: string;
};

export const YAHOO_USE_CASE_KEYS: TranslationKey[] = [
  "dcYahooUseUsStocks",
  "dcYahooUseEtfs",
  "dcYahooUseHkStocks",
  "dcYahooUseCnBasic",
  "dcYahooUseCryptoBasic",
  "dcYahooUseIndicesFxFutures",
];

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
    notesKey: "dcNoteCryptoCoinGecko",
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
  {
    id: "csv-upload",
    assetClassKey: "dcAssetCsvUpload",
    marketKey: "dcMarketCustom",
    examples: "local CSV",
    sourceKey: "dcSourcePlanned",
    status: "planned",
    notesKey: "dcNoteCsvUpload",
  },
];

export const PLANNED_PROVIDER_CARDS: PlannedProviderCard[] = [
  {
    id: "stooq",
    titleKey: "dcStooqTitle",
    descKey: "dcStooqDesc",
    status: "active",
  },
  {
    id: "coingecko",
    titleKey: "dcCoinGeckoTitle",
    descKey: "dcCoinGeckoDesc",
    status: "planned",
  },
  {
    id: "csv",
    titleKey: "dcCsvUploadTitle",
    descKey: "dcCsvUploadDesc",
    status: "planned",
  },
  {
    id: "tushare",
    titleKey: "dcTushareTitle",
    descKey: "dcTushareDesc",
    status: "comingLater",
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
    case "planned":
      return "statusPlanned";
    case "comingLater":
      return "statusComingLater";
  }
}

export function coverageStatusBadgeVariant(
  status: CoverageStatus
): "success" | "info" | "neutral" {
  switch (status) {
    case "active":
      return "success";
    case "basic":
    case "planned":
      return "info";
    case "comingLater":
      return "neutral";
  }
}
