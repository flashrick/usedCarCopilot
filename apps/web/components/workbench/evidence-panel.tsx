"use client";

import { FileText, Quote } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { truncate } from "@/lib/format";
import { compactLabel } from "@/lib/i18n";
import type { RecommendationEvidence } from "@/lib/types";

type EvidencePanelProps = {
  evidence: RecommendationEvidence[];
  highlightedIds?: string[];
};

export function EvidencePanel({ evidence, highlightedIds = [] }: EvidencePanelProps) {
  const { copy, locale } = useLocale();
  const highlightedSet = new Set(highlightedIds);

  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center gap-2">
        <Quote className="h-4 w-4 text-primaryDeep" />
        <h3 className="text-sm font-semibold">{copy.evidencePanel.title}</h3>
      </div>
      <div className="mt-3 space-y-3">
        {evidence.map((item) => (
          <article
            key={item.id}
            className={`rounded-md border p-3 text-sm transition ${
              highlightedSet.has(item.id) ? "border-primary/30 bg-primarySoft/35" : "border-line/60 bg-shell/60"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{compactLabel(item.source_type, locale)}</div>
                <div className="mt-1 font-medium">{item.title}</div>
              </div>
              <div className="rounded-md bg-white px-2 py-1 font-mono text-[11px] text-muted">{item.id}</div>
            </div>
            <p className="mt-3 text-xs leading-5 text-muted">{truncate(item.snippet, 220)}</p>
          </article>
        ))}
        {evidence.length === 0 ? (
          <div className="rounded-md border border-dashed border-line bg-shell p-4 text-sm text-muted">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {copy.evidencePanel.empty}
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
