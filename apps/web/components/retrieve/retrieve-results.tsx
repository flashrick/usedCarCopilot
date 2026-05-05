"use client";

import { useLocale } from "@/components/i18n/locale-provider";
import { formatConsumption, formatMoneyRange, truncate } from "@/lib/format";
import { compactLabel, translateValue } from "@/lib/i18n";
import type { RetrieveResponse } from "@/lib/types";

export function RetrieveResults({ data }: { data: RetrieveResponse | null }) {
  const { copy, locale } = useLocale();
  if (!data) {
    return (
      <div className="rounded-md border border-dashed border-line bg-shell p-6 text-sm text-muted">
        {copy.retrieveResults.empty}
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
      <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
        <h3 className="text-lg font-semibold">{copy.retrieveResults.listings}</h3>
        <div className="mt-4 space-y-3">
          {data.vehicle_profiles.map((profile) => (
            <article key={profile.profile_id} className="rounded-md bg-shell p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium">{profile.title}</div>
                  <div className="mt-1 text-xs text-muted">
                    {formatMoneyRange(profile.estimated_price_min_nzd, profile.estimated_price_max_nzd, locale)} ·{" "}
                    {formatConsumption(profile.fuel_consumption_l_per_100km)} · {translateValue(profile.fuel_type, locale)} ·{" "}
                    {translateValue(profile.body_type, locale)}
                  </div>
                </div>
                <span className="rounded-md bg-white px-2 py-1 text-xs text-muted">{profile.transmission.toUpperCase()}</span>
              </div>
              {profile.suitability_summary ? <p className="mt-3 text-sm text-muted">{truncate(profile.suitability_summary, 180)}</p> : null}
            </article>
          ))}
        </div>
      </section>

      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <h3 className="text-lg font-semibold">{copy.retrieveResults.knowledge}</h3>
          <div className="mt-4 space-y-3">
            {data.knowledge.map((source) => (
              <article key={source.source_id} className="rounded-md bg-shell p-3">
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{compactLabel(source.source_type, locale)}</div>
                <div className="mt-1 font-medium">{source.title}</div>
                <p className="mt-2 text-sm text-muted">{truncate(source.summary || source.text, 170)}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <h3 className="text-lg font-semibold">{copy.retrieveResults.semanticChunks}</h3>
          <div className="mt-4 space-y-3">
            {data.chunks.map((chunk) => (
              <article key={chunk.chunk_id} className="rounded-md bg-shell p-3">
                <div className="flex items-center justify-between gap-2 text-xs text-muted">
                  <span>{chunk.source_title}</span>
                  <span>{chunk.similarity ? `${Math.round(chunk.similarity * 100)}%` : copy.common.notAvailable}</span>
                </div>
                <p className="mt-2 text-sm text-muted">{truncate(chunk.text, 180)}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
