"use client";

import { useLocale } from "@/components/i18n/locale-provider";
import type { EvalSummary } from "@/lib/types";

export function EvalSummaryGrid({ summaries }: { summaries: EvalSummary[] }) {
  const { copy } = useLocale();

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4 xl:grid-cols-2">
        {summaries.map((summary, index) => (
          <section key={summary.title} className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
            <div className="text-[11px] uppercase tracking-[0.22em] text-muted">
              {index === 0 ? copy.eval.retrievalTitle : copy.eval.recommendationTitle}
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {summary.metrics.map((metric) => (
                <div key={metric.label} className="rounded-md bg-shell px-4 py-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">{metric.label}</div>
                  <div className="mt-1 text-xl font-semibold">{metric.value}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-md bg-shell p-4">
              <div className="text-sm font-medium">{copy.eval.weakestCases}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {summary.weakestCases.map((value) => (
                  <span key={value} className="rounded-md bg-white px-3 py-2 text-xs text-muted">
                    {value}
                  </span>
                ))}
              </div>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
