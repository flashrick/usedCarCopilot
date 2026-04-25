"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  Bot,
  CarFront,
  CircleDollarSign,
  ExternalLink,
  Gauge,
  Loader2,
  MapPin,
  Search,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { fetchRecommend, fetchRetrieve } from "@/lib/api";
import type { Listing, RecommendResponse, RecommendedCar, RetrieveResponse, Severity } from "@/lib/types";

const defaultQuery = "I need a reliable car under $12,000 for commuting in Auckland.";

const severityStyles: Record<Severity, string> = {
  low: "border-[#abd600]/40 bg-[#abd600]/10 text-[#d7ff4f]",
  medium: "border-[#ffcc66]/40 bg-[#ffcc66]/10 text-[#ffd68a]",
  high: "border-[#ff8f87]/40 bg-[#ff8f87]/10 text-[#ffb4ab]",
};

export default function BuyerSearchPage() {
  const [query, setQuery] = useState(defaultQuery);
  const [budget, setBudget] = useState("12000");
  const [location, setLocation] = useState("Auckland");
  const [bodyType, setBodyType] = useState("");
  const [brand, setBrand] = useState("");
  const [fuel, setFuel] = useState("");
  const [mileage, setMileage] = useState("");
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  function buildPrompt() {
    const additions = [
      budget ? `Budget up to $${budget}.` : null,
      location ? `Location: ${location}.` : null,
      bodyType ? `Body type: ${bodyType}.` : null,
      brand ? `Preferred brand: ${brand}.` : null,
      fuel ? `Fuel preference: ${fuel}.` : null,
      mileage ? `Mileage preference: under ${mileage} km.` : null,
    ].filter(Boolean);
    return [query, ...additions].join(" ");
  }

  function runSearch() {
    setError(null);
    startTransition(async () => {
      try {
        const payload = {
          query: buildPrompt(),
          max_price: budget ? Number(budget) : undefined,
          brand: brand || undefined,
          body_type: bodyType || undefined,
          location: location || undefined,
          limit: 3,
        };

        const [recommendData, retrieveData] = await Promise.all([
          fetchRecommend(payload),
          fetchRetrieve({ ...payload, limit: 8 }),
        ]);

        setRecommendation(recommendData);
        setRetrieval(retrieveData);
        setSelectedId(recommendData.recommended_cars[0]?.listing_id ?? null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Search failed. Check that the API is running.");
      }
    });
  }

  return (
    <main className="min-h-screen bg-[#0c0e12] text-[#e2e2e7]">
      <header className="border-b border-white/10 bg-[#111317]/95">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded bg-[#007aff] text-white">
              <Gauge className="h-5 w-5" />
            </div>
            <div>
              <div className="font-[var(--font-space-grotesk)] text-lg font-bold">CAR COPILOT AI</div>
              <div className="text-xs text-[#c1c6d7]">Auckland evidence engine</div>
            </div>
          </div>
          <nav className="hidden items-center gap-5 text-sm text-[#c1c6d7] md:flex">
            <a href="#search" className="hover:text-white">
              Find Cars
            </a>
            <a href="#shortlist" className="hover:text-white">
              Shortlist
            </a>
            <a href="#evidence" className="hover:text-white">
              Evidence
            </a>
            <Link href="/admin" className="rounded border border-[#00e5ff]/40 px-3 py-2 text-[#bdf4ff] hover:bg-[#00e5ff]/10">
              Admin
            </Link>
          </nav>
        </div>
      </header>

      <section
        id="search"
        className="border-b border-white/10 bg-[#111317] bg-cover bg-center"
        style={{
          backgroundImage:
            "linear-gradient(rgba(12,14,18,0.76), rgba(12,14,18,0.9)), url('https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?auto=format&fit=crop&w=1800&q=80')",
        }}
      >
        <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8 lg:py-12">
          <div className="flex min-h-[420px] flex-col justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded border border-[#00e5ff]/35 bg-[#00e5ff]/10 px-3 py-2 text-sm text-[#bdf4ff]">
                <Bot className="h-4 w-4" />
                AI Processing Active
              </div>
              <h1 className="mt-6 max-w-3xl font-[var(--font-space-grotesk)] text-4xl font-bold leading-tight text-white md:text-6xl">
                Find the right used car with AI-backed evidence
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-[#c1c6d7] md:text-lg">
                Search local listings, compare fit, and see the evidence behind every recommendation before you inspect
                or negotiate.
              </p>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <Metric label="Market scan" value={retrieval?.listings.length ? `${retrieval.listings.length} cars` : "Ready"} />
              <Metric label="Evidence" value={recommendation?.evidence.length ? `${recommendation.evidence.length} cites` : "Cited"} />
              <Metric label="Mode" value="Buyer-safe" />
            </div>
          </div>

          <section className="rounded-lg border border-white/10 bg-[#1a1c1f]/95 p-4 shadow-[0_24px_80px_rgba(0,0,0,0.32)] md:p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-[#bdf4ff]">Filters</div>
                <h2 className="font-[var(--font-space-grotesk)] text-2xl font-semibold text-white">Tell Copilot what matters</h2>
              </div>
              <Sparkles className="h-5 w-5 text-[#ccff00]" />
            </div>

            <div className="mt-5 grid gap-3">
              <label className="grid gap-2 text-sm text-[#c1c6d7]">
                Search brief
                <textarea
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  className="min-h-28 resize-none rounded border border-white/10 bg-[#111317] px-3 py-3 text-white outline-none transition focus:border-[#00e5ff] focus:ring-2 focus:ring-[#00e5ff]/20"
                />
              </label>

              <div className="grid gap-3 sm:grid-cols-2">
                <FilterInput label="Budget" value={budget} onChange={setBudget} placeholder="12000" />
                <FilterInput label="Location" value={location} onChange={setLocation} placeholder="Auckland" />
                <FilterInput label="Body Type" value={bodyType} onChange={setBodyType} placeholder="Hatchback" />
                <FilterInput label="Brand" value={brand} onChange={setBrand} placeholder="Toyota" />
                <FilterInput label="Fuel" value={fuel} onChange={setFuel} placeholder="Hybrid" />
                <FilterInput label="Mileage" value={mileage} onChange={setMileage} placeholder="90000" />
              </div>

              <button
                type="button"
                onClick={runSearch}
                disabled={isPending}
                className="mt-2 inline-flex h-12 items-center justify-center gap-2 rounded bg-[#007aff] px-5 text-sm font-semibold text-white transition hover:bg-[#238cff] disabled:cursor-not-allowed disabled:opacity-70"
              >
                {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                {isPending ? "Searching..." : "Find my best options"}
              </button>
            </div>

            {error ? (
              <div className="mt-4 flex items-start gap-3 rounded border border-[#ffb4ab]/40 bg-[#93000a]/30 p-3 text-sm text-[#ffdad6]">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}
          </section>
        </div>
      </section>

      <section id="shortlist" className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.92fr_1.08fr] lg:px-8">
        <div className="grid content-start gap-4">
          <SectionTitle eyebrow="Shortlist" title="Best matches" />
          {recommendation?.recommended_cars.length ? (
            recommendation.recommended_cars.map((car, index) => (
              <ResultCard
                key={car.listing_id}
                car={car}
                listing={listingById.get(car.listing_id)}
                rank={index + 1}
                selected={selectedCar?.listing_id === car.listing_id}
                onSelect={() => setSelectedId(car.listing_id)}
              />
            ))
          ) : (
            <EmptyPanel text="Run a search to generate your shortlist." />
          )}
        </div>

        <aside className="grid content-start gap-4">
          <SectionTitle eyebrow="Decision report" title={selectedCar?.title ?? "Select a result"} />
          {selectedCar ? (
            <DecisionPanel car={selectedCar} listing={selectedListing} evidence={recommendation?.evidence ?? []} />
          ) : (
            <EmptyPanel text="The decision report will show price context, risks, next steps, and citations." />
          )}
        </aside>
      </section>

      <section id="evidence" className="border-t border-white/10 bg-[#111317]">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <SectionTitle eyebrow="Evidence citations" title="What the recommendation engine used" />
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(recommendation?.evidence ?? []).map((item) => (
              <article key={item.id} className="rounded-lg border border-white/10 bg-[#1e2023] p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="rounded bg-[#00e5ff]/10 px-2 py-1 text-xs font-semibold text-[#bdf4ff]">{item.source_type}</span>
                  <span className="font-mono text-xs text-[#8b90a0]">{item.id}</span>
                </div>
                <h3 className="mt-3 font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{item.snippet}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-white/10 bg-[#1a1c1f]/85 p-4">
      <div className="text-sm text-[#8b90a0]">{label}</div>
      <div className="mt-2 font-[var(--font-space-grotesk)] text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="grid gap-2 text-sm text-[#c1c6d7]">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="h-11 rounded border border-white/10 bg-[#111317] px-3 text-white outline-none transition placeholder:text-[#8b90a0] focus:border-[#00e5ff] focus:ring-2 focus:ring-[#00e5ff]/20"
      />
    </label>
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
}: {
  car: RecommendedCar;
  listing?: Listing;
  rank: number;
  selected: boolean;
  onSelect: () => void;
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
            {rank === 1 ? <span className="rounded bg-[#ccff00] px-2 py-1 text-xs font-bold text-[#161e00]">Best Match</span> : null}
          </div>
          <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{car.title}</h3>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-[#c1c6d7]">
            {listing?.price ? (
              <span className="inline-flex items-center gap-1">
                <CircleDollarSign className="h-4 w-4 text-[#abd600]" /> ${listing.price.toLocaleString()}
              </span>
            ) : null}
            {listing?.location ? (
              <span className="inline-flex items-center gap-1">
                <MapPin className="h-4 w-4 text-[#00e5ff]" /> {listing.location}
              </span>
            ) : null}
            {listing?.mileage ? <span>{listing.mileage.toLocaleString()} km</span> : null}
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
        <Spec icon={CarFront} label="Year" value={listing?.year?.toString() ?? "TBC"} />
        <Spec icon={MapPin} label="Location" value={listing?.location ?? "TBC"} />
        <Spec icon={Zap} label="Fuel" value={listing?.fuel_type ?? "TBC"} />
      </div>

      <div className="mt-5">
        <h3 className="font-semibold text-white">Risk flags</h3>
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
              No major risk flags surfaced for this search.
            </div>
          )}
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="font-semibold text-white">Next steps</h3>
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
          <h3 className="font-semibold text-white">Matched citations</h3>
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
          Open listing <ExternalLink className="h-4 w-4" />
        </a>
      ) : null}
    </div>
  );
}

function ScoreGauge({ score, large = false }: { score: number; large?: boolean }) {
  const segments = Array.from({ length: 10 }, (_, index) => index < Math.round(score / 10));

  return (
    <div className={large ? "min-w-32" : "min-w-24"}>
      <div className="text-right font-[var(--font-space-grotesk)] text-3xl font-bold text-[#ccff00]">{score}</div>
      <div className="mt-2 grid grid-cols-10 gap-1">
        {segments.map((active, index) => (
          <span key={index} className={`h-2 rounded-sm ${active ? "bg-[#ccff00]" : "bg-[#333539]"}`} />
        ))}
      </div>
      <div className="mt-1 text-right text-xs text-[#8b90a0]">Match score</div>
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
  return (
    <span className="inline-flex items-center gap-2 rounded border border-white/10 bg-[#282a2e] px-2 py-1 text-xs font-semibold text-[#c1c6d7]">
      <span className="h-1.5 w-1.5 rounded-full bg-[#007aff]" />
      {label}
    </span>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return <div className="rounded-lg border border-white/10 bg-[#1a1c1f] p-5 text-sm text-[#c1c6d7]">{text}</div>;
}
