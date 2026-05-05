"use client";

import { BadgeAlert, ChevronRight, FileStack, ShieldAlert } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { severityTone } from "@/lib/format";
import { formatTemplate } from "@/lib/i18n";
import type { RecommendedProfile } from "@/lib/types";

type RecommendationCardProps = {
  car: RecommendedProfile;
  selected?: boolean;
  onSelect?: (profileId: string) => void;
};

export function RecommendationCard({ car, selected, onSelect }: RecommendationCardProps) {
  const { copy } = useLocale();
  return (
    <article
      className={`rounded-md border bg-panel p-4 shadow-panel transition ${
        selected ? "border-primary/35 ring-2 ring-primary/12" : "border-line/70"
      }`}
    >
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.recommendationCard.eyebrow}</p>
            <h3 className="mt-1 text-lg font-semibold tracking-tight">{car.title}</h3>
            <p className="mt-1 text-sm text-muted">{car.valuation_summary}</p>
            <p className="mt-2 text-xs text-muted">{car.powertrain_summary}</p>
          </div>
          <div className="rounded-xl bg-primary px-3 py-2 text-right text-white shadow-soft">
            <div className="text-[11px] uppercase tracking-[0.18em] text-white/80">{copy.recommendationCard.match}</div>
            <div className="text-xl font-semibold">{car.match_score}</div>
          </div>
        </div>

        <section className="grid gap-3 md:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-md bg-shell p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <ShieldAlert className="h-4 w-4 text-primaryDeep" />
              {copy.recommendationCard.whyItMatches}
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
              <BadgeAlert className="h-4 w-4 text-riskHighInk" />
              {copy.recommendationCard.riskFlags}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {car.risk_flags.map((flag) => (
                <span key={`${car.profile_id}-${flag.label}`} className={`rounded-md px-2 py-1 text-xs font-medium ${severityTone(flag.severity)}`}>
                  {flag.label}
                </span>
              ))}
            </div>
            <ul className="mt-3 space-y-2 text-xs text-muted">
              {car.risk_flags.map((flag) => (
                <li key={`${car.profile_id}-detail-${flag.label}`} className="rounded-md bg-white px-3 py-2">
                  {flag.reason}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
          <div className="rounded-md bg-shell p-3">
            <div className="text-sm font-medium">{copy.recommendationCard.tradeOffs}</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {car.trade_offs.map((step) => (
                <span key={`${car.profile_id}-${step}`} className="rounded-md bg-white px-3 py-2 text-xs text-muted">
                  {step}
                </span>
              ))}
            </div>
          </div>

          <div className="flex items-end justify-between gap-3 rounded-md bg-shell p-3 lg:min-w-48 lg:flex-col lg:items-stretch">
            <div className="rounded-md bg-white px-3 py-2 text-sm">
              <div className="text-[11px] uppercase tracking-[0.18em] text-muted">{copy.recommendationCard.evidence}</div>
              <div className="mt-1 flex items-center gap-2 font-medium">
                <FileStack className="h-4 w-4 text-primaryDeep" />
                {formatTemplate(copy.recommendationCard.linkedItems, { count: car.evidence_ids.length })}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onSelect?.(car.profile_id)}
              className="flex items-center justify-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-primaryDeep transition hover:border-primary/30 hover:bg-primarySoft/40"
            >
              {copy.recommendationCard.inspect}
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div className="rounded-md bg-shell p-3">
          <div className="text-sm font-medium">{copy.recommendationCard.nextSteps}</div>
          <div className="mt-2 flex flex-wrap gap-2">
            {car.next_steps.map((step) => (
              <span key={`${car.profile_id}-${step}`} className="rounded-md bg-white px-3 py-2 text-xs text-muted">
                {step}
              </span>
            ))}
          </div>
        </div>
      </div>
    </article>
  );
}
