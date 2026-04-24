"use client";

import { compactLabel, formatMileage, formatMoney, truncate } from "@/lib/format";
import type { RetrieveResponse } from "@/lib/types";

export function RetrieveResults({ data }: { data: RetrieveResponse | null }) {
  if (!data) {
    return (
      <div className="rounded-md border border-dashed border-line bg-shell p-6 text-sm text-muted">
        Run retrieval to inspect listings, linked knowledge, and semantic chunks.
      </div>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
      <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
        <h3 className="text-lg font-semibold">Listings</h3>
        <div className="mt-4 space-y-3">
          {data.listings.map((listing) => (
            <article key={listing.listing_id} className="rounded-md bg-shell p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium">{listing.title}</div>
                  <div className="mt-1 text-xs text-muted">
                    {formatMoney(listing.price)} · {formatMileage(listing.mileage)} · {listing.fuel_type ?? "N/A"} ·{" "}
                    {listing.body_type ?? "N/A"}
                  </div>
                </div>
                <span className="rounded-md bg-white px-2 py-1 text-xs text-muted">{listing.location}</span>
              </div>
              {listing.description ? <p className="mt-3 text-sm text-muted">{truncate(listing.description, 180)}</p> : null}
            </article>
          ))}
        </div>
      </section>

      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <h3 className="text-lg font-semibold">Knowledge</h3>
          <div className="mt-4 space-y-3">
            {data.knowledge.map((source) => (
              <article key={source.source_id} className="rounded-md bg-shell p-3">
                <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{compactLabel(source.source_type)}</div>
                <div className="mt-1 font-medium">{source.title}</div>
                <p className="mt-2 text-sm text-muted">{truncate(source.summary || source.text, 170)}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <h3 className="text-lg font-semibold">Semantic chunks</h3>
          <div className="mt-4 space-y-3">
            {data.chunks.map((chunk) => (
              <article key={chunk.chunk_id} className="rounded-md bg-shell p-3">
                <div className="flex items-center justify-between gap-2 text-xs text-muted">
                  <span>{chunk.source_title}</span>
                  <span>{chunk.similarity ? `${Math.round(chunk.similarity * 100)}%` : "N/A"}</span>
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
