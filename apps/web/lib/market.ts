import { localeStorageKey, type Locale } from "@/lib/i18n";
import type { Market } from "@/lib/types";

export const marketStorageKey = "used-car-copilot-market";

export function defaultMarketForLocale(locale: Locale): Market {
  return locale === "zh-CN" ? "CN" : "US";
}

export function isMarket(value: string | null | undefined): value is Market {
  return value === "US" || value === "CN";
}

export function resolveInitialMarket(locale: Locale, search: URLSearchParams): Market {
  const fromQuery = search.get("market");
  if (isMarket(fromQuery)) {
    return fromQuery;
  }
  if (typeof window !== "undefined") {
    const saved = window.localStorage.getItem(marketStorageKey);
    if (isMarket(saved)) {
      return saved;
    }
    const savedLocale = window.localStorage.getItem(localeStorageKey);
    if (savedLocale === "zh-CN") {
      return "CN";
    }
  }
  return defaultMarketForLocale(locale);
}

export function marketLabel(market: Market, locale: Locale): string {
  if (market === "CN") {
    return locale === "zh-CN" ? "中国" : "China";
  }
  return locale === "zh-CN" ? "美国" : "United States";
}
