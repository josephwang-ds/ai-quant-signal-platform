/** 行情数据源全局偏好（localStorage），默认 auto。 */

export const MARKET_DATA_SOURCES = ["auto", "akshare", "yahoo", "stooq"] as const;

export type MarketDataSource = (typeof MARKET_DATA_SOURCES)[number];

const STORAGE_KEY = "quant.marketDataSource";

export function isMarketDataSource(value: string): value is MarketDataSource {
  return (MARKET_DATA_SOURCES as readonly string[]).includes(value);
}

export function getDataSourcePreference(): MarketDataSource {
  if (typeof window === "undefined") {
    return "auto";
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)?.trim().toLowerCase();
    if (raw && isMarketDataSource(raw)) {
      return raw;
    }
  } catch {
    // 忽略隐私模式等读写失败
  }
  return "auto";
}

export function setDataSourcePreference(source: MarketDataSource): void {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, source);
  } catch {
    // 忽略隐私模式等读写失败
  }
}
