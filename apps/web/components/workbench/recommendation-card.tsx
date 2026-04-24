"use client";

import { BadgeAlert, ChevronRight, FileStack, ShieldAlert } from "lucide-react";
import { formatMoney, severityTone } from "@/lib/format";
import type { RecommendedCar } from "@/lib/types";

type RecommendationCardProps = {
  car: RecommendedCar;
  selected?: boolean;
  onSelect?: (listingId: string) => void;
};

export function RecommendationCard({ car, selected, onSelect }: RecommendationCardProps) {
  return (
    <article
      className={`rounded-md border bg-panel p-4 shadow-panel transition ${
        selected ? "border-steel/40 ring-2 ring-steel/20" : "border-line/70"
      }`}
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-muted">Recommendation</p>
            <h3 className="mt-1 text-lg font-semibold tracking-tight">{car.title}</h3>
            <p className="mt-1 text-sm text-muted">{car.price_commentary}</p>
          </div>
          <div className="rounded-md bg-steelDeep px-3 py-2 text-right text-white shadow-inset">
            <div className="text-[11px] uppercase tracking-[0.18em] text-white/70">Match</div>
            <div className="text-xl font-semibold">{car.match_score}</div>
          </div>
        </div>

        <section className="grid gap-3 md:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md bg-shell p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <ShieldAlert className="h-4 w-4 text-steelDeep" />
              Why it matches
            </div>
            <ul className="mt-2 space-y-2 text-sm text-ink/90">
              {car.why_it_matches.map((reason) => (
                <li key={reason} className="rounded-md bg-white px-3 py-2">
                  {reason}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-md bg-shell p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <BadgeAlert className="h-4 w-4 text-[#8e3134]" />
              Risk flags
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {car.risk_flags.map((flag) => (
                <span key={`${car.listing_id}-${flag.label}`} className={`rounded-md px-2 py-1 text-xs font-medium ${severityTone(flag.severity)}`}>
                  {flag.label}
                </span>
              ))}
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted">
              {car.risk_flags.map((flag) => (
                <li key={`${car.listing_id}-detail-${flag.label}`} className="rounded-md bg-white px-3 py-2">
                  {flag.reason}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          <div className="rounded-md bg-shell p-3">
            <div className="text-sm font-medium">Next steps</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {car.next_steps.map((step) => (
                <span key={`${car.listing_id}-${step}`} className="rounded-md bg-white px-3 py-2 text-xs text-muted">
                  {step}
                </span>
              ))}
            </div>
          </div>

          <div className="flex items-end justify-between gap-3 rounded-md bg-shell p-3 lg:min-w-48 lg:flex-col lg:items-stretch">
            <div className="rounded-md bg-white px-3 py-2 text-sm">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted">Evidence</div>
              <div className="mt-1 flex items-center gap-2 font-medium">
                <FileStack className="h-4 w-4 text-steelDeep" />
                {car.evidence_ids.length} linked items
              </div>
            </div>
            <button
              type="button"
              onClick={() => onSelect?.(car.listing_id)}
              className="flex items-center justify-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-steelDeep transition hover:border-steel/40 hover:bg-steelSoft/50"
            >
              Inspect
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}
