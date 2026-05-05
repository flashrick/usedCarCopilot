"use client";

import { useEffect, useState, useTransition } from "react";
import { AlertTriangle } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { QueryComposer } from "@/components/workbench/query-composer";
import { RecommendationCard } from "@/components/workbench/recommendation-card";
import { EvidencePanel } from "@/components/workbench/evidence-panel";
import { DebugPanel } from "@/components/workbench/debug-panel";
import { ComparisonMatrix } from "@/components/workbench/comparison-matrix";
import { RetrievalTable } from "@/components/workbench/retrieval-table";
import { fetchRecommend, fetchRetrieve } from "@/lib/api";
import { parseIntegerInput } from "@/lib/form";
import type { RecommendResponse, RetrieveResponse } from "@/lib/types";

const defaultQuery = "I need a reliable car under $12,000 for commuting in Auckland.";

export default function HomePage() {
  const { copy } = useLocale();
  const [query, setQuery] = useState(defaultQuery);
  const [budget, setBudget] = useState("12000");
  const [brand, setBrand] = useState("");
  const [bodyType, setBodyType] = useState("");
  const [location, setLocation] = useState("Auckland");
  const [selectedListingIds, setSelectedListingIds] = useState<string[]>([]);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRetrieving, startRetrieval] = useTransition();
  const [isAdvising, startAdvice] = useTransition();

  useEffect(() => {
    runWorkbenchQuery();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function runWorkbenchQuery() {
    setError(null);
    startRetrieval(async () => {
      try {
        const maxPrice = parseIntegerInput(budget);
        const payload = {
          query,
          max_price: maxPrice,
          brand: brand || undefined,
          body_type: bodyType || undefined,
          location: location || undefined,
          limit: 20,
        };

        const retrieveData = await fetchRetrieve(payload);

        setRetrieval(retrieveData);
        setRecommendation(null);
        setSelectedListingIds([]);
        setSelectedRecommendationId(null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : copy.adminWorkbench.defaultError);
      }
    });
  }

  function toggleSelection(listingId: string) {
    setError(null);
    setSelectedRecommendationId(null);
    setRecommendation(null);
    setSelectedListingIds((current) => {
      if (current.includes(listingId)) {
        return current.filter((value) => value !== listingId);
      }
      if (current.length >= 4) {
        setError(copy.adminWorkbench.selectionLimitError);
        return current;
      }
      return [...current, listingId];
    });
  }

  function requestAdvice() {
    if (selectedListingIds.length < 2) {
      setError(copy.adminWorkbench.selectionMinimumError);
      return;
    }

    setError(null);
    startAdvice(async () => {
      try {
        const recommendData = await fetchRecommend({
          query,
          selected_listing_ids: selectedListingIds,
        });
        setRecommendation(recommendData);
        setSelectedRecommendationId(recommendData.recommended_cars[0]?.listing_id ?? null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : copy.adminWorkbench.defaultError);
      }
    });
  }

  const selectedCar =
    recommendation?.recommended_cars.find((car) => car.listing_id === selectedRecommendationId) ??
    recommendation?.recommended_cars[0] ??
    null;

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <QueryComposer
          query={query}
          budget={budget}
          brand={brand}
          bodyType={bodyType}
          location={location}
          onQueryChange={setQuery}
          onBudgetChange={setBudget}
          onBrandChange={setBrand}
          onBodyTypeChange={setBodyType}
          onLocationChange={setLocation}
          onSubmit={runWorkbenchQuery}
          loading={isRetrieving}
        />

        {error ? (
          <div className="flex items-center gap-3 rounded-md border border-riskHigh/70 bg-[#fff1f1] px-4 py-3 text-sm text-rose-900">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[1.45fr_0.78fr]">
          <section className="grid gap-4">
            <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.adminWorkbench.shortlistEyebrow}</div>
                  <h3 className="mt-1 text-lg font-semibold">{copy.adminWorkbench.shortlistTitle}</h3>
                  <p className="mt-2 text-sm text-muted">{copy.adminWorkbench.selectionHint}</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <div className="rounded-md bg-shell px-3 py-2 text-xs text-muted">
                    {copy.adminWorkbench.selectedCount.replace("{count}", String(selectedListingIds.length))}
                  </div>
                  <button
                    type="button"
                    onClick={requestAdvice}
                    disabled={isAdvising || selectedListingIds.length < 2}
                    className="flex h-11 items-center justify-center rounded-md bg-gradient-to-b from-steel to-steelDeep px-4 text-sm font-medium text-white shadow-panel transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isAdvising ? copy.adminWorkbench.advising : copy.adminWorkbench.getAdvice}
                  </button>
                </div>
              </div>
              <div className="mt-4">
                <RetrievalTable
                  listings={retrieval?.listings ?? []}
                  selectedListingIds={selectedListingIds}
                  onToggleSelection={toggleSelection}
                />
              </div>
            </section>

            {recommendation?.recommended_cars.length ? (
              recommendation.recommended_cars.map((car) => (
                <RecommendationCard
                  key={car.listing_id}
                  car={car}
                  selected={car.listing_id === selectedCar?.listing_id}
                  onSelect={setSelectedRecommendationId}
                />
              ))
            ) : (
              <section className="rounded-md border border-dashed border-line/70 bg-panel p-4 text-sm text-muted">
                {copy.adminWorkbench.emptyRecommendation}
              </section>
            )}
          </section>

          <section className="grid gap-4">
            <EvidencePanel evidence={recommendation?.evidence ?? []} highlightedIds={selectedCar?.evidence_ids ?? []} />
            <DebugPanel debug={recommendation?.debug ?? { state: copy.adminWorkbench.emptyDebug }} />
          </section>
        </div>

        <div className="grid gap-4">
          <ComparisonMatrix cars={recommendation?.recommended_cars ?? []} />
        </div>
      </div>
    </div>
  );
}
