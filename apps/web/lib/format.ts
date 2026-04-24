import type { Severity } from "@/lib/types";

export function formatMoney(value?: number | null): string {
  if (value === null || value === undefined) return "N/A";
  return new Intl.NumberFormat("en-NZ", {
    style: "currency",
    currency: "NZD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatMileage(value?: number | null): string {
  if (value === null || value === undefined) return "N/A";
  return `${new Intl.NumberFormat("en-NZ").format(value)} km`;
}

export function severityTone(severity: Severity): string {
  if (severity === "high") return "bg-riskHigh/70 text-rose-950";
  if (severity === "medium") return "bg-riskMedium/80 text-amber-950";
  return "bg-riskLow/90 text-orange-950";
}

export function compactLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function truncate(value: string, length = 140): string {
  if (value.length <= length) return value;
  return `${value.slice(0, length - 3).trimEnd()}...`;
}
