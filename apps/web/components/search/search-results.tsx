"use client";

import {
  ArrowRight,
  BadgeCheck,
  CarFront,
  CircleDollarSign,
  MapPin,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { formatMileage, formatMoney } from "@/lib/format";
import { compactLabel, formatTemplate, translateValue } from "@/lib/i18n";
import type { Listing, RecommendResponse, RetrieveResponse, Severity } from "@/lib/types";

type SearchResultsProps = {
  recommendation: RecommendResponse | null;
  retrieval: RetrieveResponse | null;
  selectedListingIds: string[];
  onToggleSelection: (id: string) => void;
  onRequestAdvice: () => void;
  recommendationLoading?: boolean;
};

const severityStyles: Record<Severity, string> = {
  low: "border-[#abd600]/40 bg-[#abd600]/10 text-[#d7ff4f]",
  medium: "border-[#ffcc66]/40 bg-[#ffcc66]/10 text-[#ffd68a]",
  high: "border-[#ff8f87]/40 bg-[#ff8f87]/10 text-[#ffb4ab]",
};

export function SearchResults({
  recommendation,
  retrieval,
  selectedListingIds,
  onToggleSelection,
  onRequestAdvice,
  recommendationLoading,
}: SearchResultsProps) {
  const { copy, locale } = useLocale();
  const selectedSet = new Set(selectedListingIds);

  return (
    <>
      <section id="shortlist" className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.94fr_1.06fr]">
        <div className="grid content-start gap-4">
          <SectionTitle eyebrow={copy.searchResults.shortlist} title={copy.searchResults.bestMatches} />
          <SelectionToolbar
            count={selectedListingIds.length}
            countLabel={copy.searchResults.selectedCount}
            helper={copy.searchResults.selectionHint}
            buttonLabel={copy.searchResults.getAdvice}
            buttonLoadingLabel={copy.searchResults.adviceLoading}
            disabled={selectedListingIds.length < 2 || Boolean(recommendationLoading)}
            loading={recommendationLoading}
            onRequestAdvice={onRequestAdvice}
          />
          {retrieval?.listings.length ? (
            retrieval.listings.map((listing, index) => (
              <ShortlistCard
                key={listing.listing_id}
                listing={listing}
                rank={index + 1}
                selected={selectedSet.has(listing.listing_id)}
                onToggle={() => onToggleSelection(listing.listing_id)}
                locale={locale}
                selectLabel={copy.searchResults.selectLabel}
                selectedLabel={copy.searchResults.selectedBadge}
                bodyLabel={copy.queryComposer.body}
                fuelLabel={copy.searchResults.fuel}
                yearLabel={copy.searchResults.year}
                tbcLabel={copy.searchResults.tbc}
              />
            ))
          ) : (
            <EmptyPanel text={copy.searchResults.emptyShortlist} />
          )}
        </div>

        <aside id="advice" className="grid content-start gap-4">
          <SectionTitle eyebrow={copy.searchResults.aiAdvice} title={copy.searchResults.aiAdviceTitle} />
          {recommendation?.recommended_cars.length ? (
            recommendation.recommended_cars.map((car, index) => (
              <article key={car.listing_id} className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded bg-[#007aff] px-2 py-1 text-xs font-bold text-white">#{index + 1}</span>
                      {index === 0 ? (
                        <span className="rounded bg-[#ccff00] px-2 py-1 text-xs font-bold text-[#161e00]">
                          {copy.searchResults.bestMatchBadge}
                        </span>
                      ) : null}
                    </div>
                    <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{car.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{car.price_commentary}</p>
                  </div>
                  <ScoreGauge score={car.match_score} />
                </div>

                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-semibold text-white">{copy.searchResults.matchReasons}</h4>
                    <div className="mt-3 grid gap-2">
                      {car.why_it_matches.map((reason) => (
                        <div key={reason} className="flex items-start gap-2 text-sm leading-6 text-[#c1c6d7]">
                          <BadgeCheck className="mt-1 h-4 w-4 shrink-0 text-[#ccff00]" />
                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-white">{copy.searchResults.riskFlags}</h4>
                    <div className="mt-3 grid gap-2">
                      {car.risk_flags.length ? (
                        car.risk_flags.map((flag) => (
                          <div key={`${flag.label}-${flag.reason}`} className={`rounded border p-3 text-sm ${severityStyles[flag.severity]}`}>
                            <div className="font-semibold">{flag.label}</div>
                            <div className="mt-1 leading-6">{flag.reason}</div>
                          </div>
                        ))
                      ) : (
                        <div className="rounded border border-[#abd600]/40 bg-[#abd600]/10 p-3 text-sm text-[#d7ff4f]">
                          {copy.searchResults.noMajorRisk}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <MetaTile icon={CarFront} label={copy.searchResults.matchScore} value={String(car.match_score)} />
                  <MetaTile icon={ShieldCheck} label={copy.searchResults.matchedCitations} value={String(car.evidence_ids.length)} />
                  <MetaTile icon={ArrowRight} label={copy.searchResults.nextSteps} value={String(car.next_steps.length)} />
                </div>

                <div className="mt-5">
                  <h4 className="font-semibold text-white">{copy.searchResults.nextSteps}</h4>
                  <div className="mt-3 grid gap-2">
                    {car.next_steps.map((step) => (
                      <div key={step} className="flex items-start gap-2 text-sm leading-6 text-[#c1c6d7]">
                        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-[#00e5ff]" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </article>
            ))
          ) : (
            <EmptyPanel text={copy.searchResults.emptyAdvice} />
          )}
        </aside>
      </section>

      <section id="evidence" className="border-t border-white/10 bg-[#111317]">
        <div className="mx-auto max-w-7xl py-8">
          <SectionTitle eyebrow={copy.searchResults.evidenceEyebrow} title={copy.searchResults.evidenceTitle} />
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(recommendation?.evidence ?? []).map((item) => (
              <article key={item.id} className="rounded-lg border border-white/10 bg-[#1e2023] p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="rounded bg-[#00e5ff]/10 px-2 py-1 text-xs font-semibold text-[#bdf4ff]">{compactLabel(item.source_type, locale)}</span>
                  <span className="font-mono text-xs text-[#8b90a0]">{item.id}</span>
                </div>
                <h3 className="mt-3 font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{item.snippet}</p>
              </article>
            ))}
            {recommendation?.evidence.length ? null : <EmptyPanel text={copy.searchResults.emptyEvidence} />}
          </div>
        </div>
      </section>
    </>
  );
}

function SelectionToolbar({
  count,
  countLabel,
  helper,
  buttonLabel,
  buttonLoadingLabel,
  disabled,
  loading,
  onRequestAdvice,
}: {
  count: number;
  countLabel: string;
  helper: string;
  buttonLabel: string;
  buttonLoadingLabel: string;
  disabled: boolean;
  loading?: boolean;
  onRequestAdvice: () => void;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-white">{formatTemplate(countLabel, { count })}</div>
          <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{helper}</p>
        </div>
        <button
          type="button"
          onClick={onRequestAdvice}
          disabled={disabled}
          className="inline-flex h-11 items-center justify-center rounded bg-[#00a8ff] px-5 text-sm font-semibold text-white transition hover:bg-[#2ab7ff] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? buttonLoadingLabel : buttonLabel}
        </button>
      </div>
    </div>
  );
}

function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <div className="text-sm font-semibold text-[#bdf4ff]">{eyebrow}</div>
      <h2 className="mt-1 font-[var(--font-space-grotesk)] text-2xl font-semibold text-white">{title}</h2>
    </div>
  );
}

function ShortlistCard({
  listing,
  rank,
  selected,
  onToggle,
  locale,
  selectLabel,
  selectedLabel,
  bodyLabel,
  fuelLabel,
  yearLabel,
  tbcLabel,
}: {
  listing: Listing;
  rank: number;
  selected: boolean;
  onToggle: () => void;
  locale: "en" | "zh-CN";
  selectLabel: string;
  selectedLabel: string;
  bodyLabel: string;
  fuelLabel: string;
  yearLabel: string;
  tbcLabel: string;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`w-full rounded-lg border p-4 text-left transition ${
        selected ? "border-[#00e5ff] bg-[#1e2023]" : "border-white/10 bg-[#1a1c1f] hover:border-[#00e5ff]/50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-[#007aff] px-2 py-1 text-xs font-bold text-white">#{rank}</span>
            <span
              className={`rounded px-2 py-1 text-xs font-bold ${
                selected ? "bg-[#ccff00] text-[#161e00]" : "bg-white/8 text-[#d6e3f2]"
              }`}
            >
              {selected ? selectedLabel : selectLabel}
            </span>
          </div>
          <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{listing.title}</h3>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-[#c1c6d7]">
            {listing.price ? (
              <span className="inline-flex items-center gap-1">
                <CircleDollarSign className="h-4 w-4 text-[#abd600]" /> {formatMoney(listing.price, locale)}
              </span>
            ) : null}
            {listing.location ? (
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-4 w-4 text-[#00e5ff]" /> {listing.location}
              </span>
            ) : null}
            {listing.mileage ? <span>{formatMileage(listing.mileage, locale)}</span> : null}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <MetaTile icon={CarFront} label={bodyLabel} value={translateValue(listing.body_type, locale)} />
        <MetaTile icon={Zap} label={fuelLabel} value={translateValue(listing.fuel_type, locale)} />
        <MetaTile icon={ShieldCheck} label={yearLabel} value={listing.year?.toString() ?? tbcLabel} />
      </div>
    </button>
  );
}

function MetaTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof CarFront;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#111317] p-3">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#8b90a0]">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <div className="mt-2 text-sm text-white">{value}</div>
    </div>
  );
}

function ScoreGauge({ score }: { score: number }) {
  return (
    <div className="rounded-full border border-[#00e5ff]/30 bg-[#00e5ff]/10 px-4 py-3 text-center">
      <div className="text-[11px] uppercase tracking-[0.18em] text-[#9ddfff]">Score</div>
      <div className="mt-1 text-2xl font-semibold text-white">{score}</div>
    </div>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-white/12 bg-[#151b22] p-5 text-sm leading-6 text-[#c1c6d7]">
      {text}
    </div>
  );
}
