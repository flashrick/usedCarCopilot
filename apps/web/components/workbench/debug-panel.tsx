"use client";

import { Cpu, ShieldCheck } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { compactLabel } from "@/lib/i18n";

export function DebugPanel({ debug }: { debug: Record<string, unknown> }) {
  const { copy, locale } = useLocale();
  const entries = Object.entries(debug).filter(([, value]) => value !== null && value !== undefined && value !== "");

  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center gap-2">
        <Cpu className="h-4 w-4 text-primaryDeep" />
        <h3 className="text-sm font-semibold">{copy.debugPanel.title}</h3>
      </div>

      <div className="mt-3 grid gap-2">
        {entries.map(([key, value]) => (
          <div key={key} className="grid grid-cols-[auto_1fr] items-start gap-3 rounded-md bg-shell px-3 py-2 text-xs">
            <span className="font-medium text-ink">{compactLabel(key, locale)}</span>
            <span className="font-mono text-muted">{formatValue(value)}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-2 rounded-md bg-primarySoft/60 px-3 py-2 text-xs text-muted">
        <ShieldCheck className="h-4 w-4 text-primaryDeep" />
        {copy.debugPanel.note}
      </div>
    </section>
  );
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
