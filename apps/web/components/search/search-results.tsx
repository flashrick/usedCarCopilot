"use client";

import { useMemo } from "react";
import {
  ArrowRight,
  BadgeCheck,
  CarFront,
  CircleDollarSign,
  ExternalLink,
  MapPin,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { formatMileage, formatMoney } from "@/lib/format";
import { compactLabel, translateValue } from "@/lib/i18n";
import type { Listing, RecommendResponse, RecommendedCar, RetrieveResponse, Severity } from "@/lib/types";

type SearchResultsProps = {
  recommendation: RecommendResponse | null;
  retrieval: RetrieveResponse | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
};

const severityStyles: Record<Severity, string> = {
  low: "border-[#abd600]/40 bg-[#abd600]/10 text-[#d7ff4f]",
  medium: "border-[#ffcc66]/40 bg-[#ffcc66]/10 text-[#ffd68a]",
  high: "border-[#ff8f87]/40 bg-[#ff8f87]/10 text-[#ffb4ab]",
};

export function SearchResults({ recommendation, retrieval, selectedId, onSelect }: SearchResultsProps) {
  const { copy, locale } = useLocale();
  const listingById = useMemo(() => {
    const map = new Map<string, Listing>();
    retrieval?.listings.forEach((listing) => map.set(listing.listing_id, listing));
    return map;
  }, [retrieval]);

  const selectedCar =
    recommendation?.recommended_cars.find((car) => car.listing_id === selectedId) ??
    recommendation?.recommended_cars[0] ??
    null;

  const selectedListing = selectedCar ? listingById.get(selectedCar.listing_id) : null;

  return (
    <>
      <section id="shortlist" className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="grid content-start gap-4">
          <SectionTitle eyebrow={copy.searchResults.shortlist} title={copy.searchResults.bestMatches} />
          {recommendation?.recommended_cars.length ? (
            recommendation.recommended_cars.map((car, index) => (
              <ResultCard
                key={car.listing_id}
                car={car}
                listing={listingById.get(car.listing_id)}
                rank={index + 1}
                selected={selectedCar?.listing_id === car.listing_id}
                onSelect={() => onSelect(car.listing_id)}
                locale={locale}
                bestMatchLabel={copy.searchResults.bestMatchBadge}
              />
            ))
          ) : (
            <EmptyPanel text={copy.searchResults.emptyShortlist} />
          )}
        </div>

        <aside className="grid content-start gap-4">
          <SectionTitle eyebrow={copy.searchResults.decisionReport} title={selectedCar?.title ?? copy.searchResults.selectAResult} />
          {selectedCar ? (
            <DecisionPanel car={selectedCar} listing={selectedListing} evidence={recommendation?.evidence ?? []} />
          ) : (
            <EmptyPanel text={copy.searchResults.emptyDecision} />
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
          </div>
        </div>
      </section>
    </>
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

function ResultCard({
  car,
  listing,
  rank,
  selected,
  onSelect,
  locale,
  bestMatchLabel,
}: {
  car: RecommendedCar;
  listing?: Listing;
  rank: number;
  selected: boolean;
  onSelect: () => void;
  locale: "en" | "zh-CN";
  bestMatchLabel: string;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-lg border p-4 text-left transition ${
        selected ? "border-[#00e5ff] bg-[#1e2023]" : "border-white/10 bg-[#1a1c1f] hover:border-[#00e5ff]/50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-[#007aff] px-2 py-1 text-xs font-bold text-white">#{rank}</span>
            {rank === 1 ? <span className="rounded bg-[#ccff00] px-2 py-1 text-xs font-bold text-[#161e00]">{bestMatchLabel}</span> : null}
          </div>
          <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{car.title}</h3>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-[#c1c6d7]">
            {listing?.price ? (
              <span className="inline-flex items-center gap-1">
                <CircleDollarSign className="h-4 w-4 text-[#abd600]" /> {formatMoney(listing.price, locale)}
              </span>
            ) : null}
            {listing?.location ? (
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-4 w-4 text-[#00e5ff]" /> {listing.location}
              </span>
            ) : null}
            {listing?.mileage ? <span>{formatMileage(listing.mileage, locale)}</span> : null}
          </div>
        </div>
        <ScoreGauge score={car.match_score} />
      </div>

      <div className="mt-4 grid gap-2">
        {car.why_it_matches.slice(0, 2).map((reason) => (
          <div key={reason} className="flex items-start gap-2 text-sm leading-6 text-[#c1c6d7]">
            <BadgeCheck className="mt-1 h-4 w-4 shrink-0 text-[#ccff00]" />
            <span>{reason}</span>
          </div>
        ))}
      </div>
    </button>
  );
}

function DecisionPanel({
  car,
  listing,
  evidence,
}: {
  car: RecommendedCar;
  listing?: Listing | null;
  evidence: RecommendResponse["evidence"];
}) {
  const highlightedEvidence = evidence.filter((item) => car.evidence_ids.includes(item.id));
  const { copy, locale } = useLocale();

  return (
    <div className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4">
      <div className="grid gap-4 md:grid-cols-[1fr_auto]">
        <div>
          <div className="flex flex-wrap gap-2">
            {listing?.body_type ? <Chip label={listing.body_type} /> : null}
            {listing?.fuel_type ? <Chip label={listing.fuel_type} /> : null}
            {listing?.transmission ? <Chip label={listing.transmission} /> : null}
          </div>
          <p className="mt-4 text-sm leading-6 text-[#c1c6d7]">{car.price_commentary}</p>
        </div>
        <ScoreGauge score={car.match_score} large />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <Spec icon={CarFront} label={copy.searchResults.year} value={listing?.year?.toString() ?? copy.searchResults.tbc} />
        <Spec icon={MapPin} label={copy.searchResults.location} value={listing?.location ?? copy.searchResults.tbc} />
        <Spec icon={Zap} label={copy.searchResults.fuel} value={translateValue(listing?.fuel_type, locale) || copy.searchResults.tbc} />
      </div>

      <div className="mt-5">
        <h3 className="font-semibold text-white">{copy.searchResults.riskFlags}</h3>
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

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="font-semibold text-white">{copy.searchResults.nextSteps}</h3>
          <div className="mt-3 grid gap-2">
            {car.next_steps.map((step) => (
              <div key={step} className="flex items-start gap-2 text-sm leading-6 text-[#c1c6d7]">
                <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-[#00e5ff]" />
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <h3 className="font-semibold text-white">{copy.searchResults.matchedCitations}</h3>
          <div className="mt-3 grid gap-2">
            {highlightedEvidence.slice(0, 3).map((item) => (
              <div key={item.id} className="rounded border border-white/10 bg-[#111317] p-3 text-sm">
                <div className="flex items-center gap-2 font-semibold text-white">
                  <ShieldCheck className="h-4 w-4 text-[#ccff00]" />
                  {item.title}
                </div>
                <p className="mt-2 leading-6 text-[#c1c6d7]">{item.snippet}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {listing?.source_url ? (
        <a
          href={listing.source_url}
          target="_blank"
          rel="noreferrer"
          className="mt-5 inline-flex items-center gap-2 rounded border border-[#00e5ff]/40 px-4 py-2 text-sm font-semibold text-[#bdf4ff] hover:bg-[#00e5ff]/10"
        >
          {copy.searchResults.openListing} <ExternalLink className="h-4 w-4" />
        </a>
      ) : null}
    </div>
  );
}

function ScoreGauge({ score, large = false }: { score: number; large?: boolean }) {
  const { copy } = useLocale();
  const segments = Array.from({ length: 10 }, (_, index) => index < Math.round(score / 10));

  return (
    <div className={large ? "min-w-32" : "min-w-24"}>
      <div className="text-right font-[var(--font-space-grotesk)] text-3xl font-bold text-[#ccff00]">{score}</div>
      <div className="mt-2 grid grid-cols-10 gap-1">
        {segments.map((active, index) => (
          <span key={index} className={`h-2 rounded-sm ${active ? "bg-[#ccff00]" : "bg-[#333539]"}`} />
        ))}
      </div>
      <div className="mt-1 text-right text-xs text-[#8b90a0]">{copy.searchResults.matchScore}</div>
    </div>
  );
}

function Spec({ icon: Icon, label, value }: { icon: typeof CarFront; label: string; value: string }) {
  return (
    <div className="rounded border border-white/10 bg-[#111317] p-3">
      <Icon className="h-4 w-4 text-[#00e5ff]" />
      <div className="mt-2 text-xs text-[#8b90a0]">{label}</div>
      <div className="mt-1 text-sm font-semibold text-white">{value}</div>
    </div>
  );
}

function Chip({ label }: { label: string }) {
  const { locale } = useLocale();
  return (
    <span className="inline-flex items-center gap-2 rounded border border-white/10 bg-[#282a2e] px-2 py-1 text-xs font-semibold text-[#c1c6d7]">
      <span className="h-1.5 w-1.5 rounded-full bg-[#007aff]" />
      {translateValue(label, locale)}
    </span>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return <div className="rounded-lg border border-white/10 bg-[#1a1c1f] p-5 text-sm text-[#c1c6d7]">{text}</div>;
}
