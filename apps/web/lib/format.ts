import { defaultLocale, translateValue, type Locale } from "@/lib/i18n";
import type { Severity } from "@/lib/types";

export function formatMoney(value?: number | null, locale: Locale = defaultLocale): string {
  if (value === null || value === undefined) return translateValue(null, locale);
  return new Intl.NumberFormat(locale === "zh-CN" ? "zh-CN" : "en-NZ", {
    style: "currency",
    currency: "NZD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatMileage(value?: number | null, locale: Locale = defaultLocale): string {
  if (value === null || value === undefined) return translateValue(null, locale);
  return `${new Intl.NumberFormat(locale === "zh-CN" ? "zh-CN" : "en-NZ").format(value)} km`;
}

export function severityTone(severity: Severity): string {
  if (severity === "high") return "bg-riskHigh/70 text-rose-950";
  if (severity === "medium") return "bg-riskMedium/80 text-amber-950";
  return "bg-riskLow/90 text-orange-950";
}

export function truncate(value: string, length = 140): string {
  if (value.length <= length) return value;
  return `${value.slice(0, length - 3).trimEnd()}...`;
}
