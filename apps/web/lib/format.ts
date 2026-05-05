import { defaultLocale, translateValue, type Locale } from "@/lib/i18n";
import type { Severity } from "@/lib/types";

function currencyForMarket(market?: string | null): string {
  if (market === "CN") return "CNY";
  if (market === "US") return "USD";
  return "NZD";
}

function localeForMoney(locale: Locale, market?: string | null): string {
  if (market === "CN") return "zh-CN";
  if (market === "US") return locale === "zh-CN" ? "zh-CN" : "en-US";
  return locale === "zh-CN" ? "zh-CN" : "en-NZ";
}

export function formatMoney(value?: number | null, locale: Locale = defaultLocale, market?: string | null): string {
  if (value === null || value === undefined) return translateValue(null, locale);
  return new Intl.NumberFormat(localeForMoney(locale, market), {
    style: "currency",
    currency: currencyForMarket(market),
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatMileage(value?: number | null, locale: Locale = defaultLocale): string {
  if (value === null || value === undefined) return translateValue(null, locale);
  return `${new Intl.NumberFormat(locale === "zh-CN" ? "zh-CN" : "en-NZ").format(value)} km`;
}

export function formatMoneyRange(
  minimum?: number | null,
  maximum?: number | null,
  locale: Locale = defaultLocale,
  market?: string | null,
): string {
  if (minimum === null || minimum === undefined || maximum === null || maximum === undefined) {
    return translateValue(null, locale);
  }
  return `${formatMoney(minimum, locale, market)} - ${formatMoney(maximum, locale, market)}`;
}

export function formatConsumption(value?: number | null): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(1)} L/100km`;
}

export function severityTone(severity: Severity): string {
  if (severity === "high") return "bg-riskHigh text-riskHighInk";
  if (severity === "medium") return "bg-riskMedium text-riskMediumInk";
  return "bg-riskLow text-riskLowInk";
}

export function truncate(value: string, length = 140): string {
  if (value.length <= length) return value;
  return `${value.slice(0, length - 3).trimEnd()}...`;
}
