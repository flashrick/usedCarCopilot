"use client";

import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { QueryComposer } from "@/components/workbench/query-composer";
import { ComparisonMatrix } from "@/components/workbench/comparison-matrix";
import { RecommendationCard } from "@/components/workbench/recommendation-card";
import { RetrievalTable } from "@/components/workbench/retrieval-table";
import { fetchRecommend, fetchRetrieve } from "@/lib/api";
import { parseIntegerInput } from "@/lib/form";
import type { RecommendResponse, RetrieveResponse } from "@/lib/types";

const defaultQuery = "Which shortlisted cars best fit daily commuting and easy parking in Auckland?";

export default function ComparePage() {
  const { copy } = useLocale();
  const [query, setQuery] = useState(defaultQuery);
  const [budget, setBudget] = useState("12000");
  const [brand, setBrand] = useState("");
  const [bodyType, setBodyType] = useState("");
  const [location, setLocation] = useState("Auckland");
  const [selectedListingIds, setSelectedListingIds] = useState<string[]>([]);
  const [selectedRecommendationId, setSelectedRecommendationId] = useState<string | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRetrieving, setIsRetrieving] = useState(false);
  const [isAdvising, setIsAdvising] = useState(false);

  async function runRetrieval() {
    setError(null);
    setIsRetrieving(true);
    try {
      const response = await fetchRetrieve({
        query,
        max_price: parseIntegerInput(budget),
        brand: brand || undefined,
        body_type: bodyType || undefined,
        location: location || undefined,
        limit: 20,
      });
      setRetrieval(response);
      setRecommendation(null);
      setSelectedListingIds([]);
      setSelectedRecommendationId(null);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : copy.adminCompare.defaultError);
    } finally {
      setIsRetrieving(false);
    }
  }

  function toggleSelection(listingId: string) {
    setError(null);
    setRecommendation(null);
    setSelectedRecommendationId(null);
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

  async function requestAdvice() {
    if (selectedListingIds.length < 2) {
      setError(copy.adminWorkbench.selectionMinimumError);
      return;
    }

    setError(null);
    setIsAdvising(true);
    try {
      const response = await fetchRecommend({
        query,
        selected_listing_ids: selectedListingIds,
      });
      setRecommendation(response);
      setSelectedRecommendationId(response.recommended_cars[0]?.listing_id ?? null);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : copy.adminCompare.defaultError);
    } finally {
      setIsAdvising(false);
    }
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
          onSubmit={() => void runRetrieval()}
          loading={isRetrieving}
        />

        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.adminCompare.eyebrow}</div>
          <h2 className="mt-1 text-2xl font-semibold">{copy.adminCompare.title}</h2>
          <p className="mt-2 max-w-3xl text-sm text-muted">{copy.adminCompare.description}</p>
          {error ? (
            <div className="mt-3 flex items-center gap-3 rounded-md border border-riskHigh/70 bg-[#fff1f1] px-4 py-3 text-sm text-rose-900">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          ) : null}
        </section>

        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.adminWorkbench.shortlistEyebrow}</div>
              <h3 className="mt-1 text-lg font-semibold">{copy.adminWorkbench.shortlistTitle}</h3>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="rounded-md bg-shell px-3 py-2 text-xs text-muted">
                {copy.adminWorkbench.selectedCount.replace("{count}", String(selectedListingIds.length))}
              </div>
              <button
                type="button"
                onClick={() => void requestAdvice()}
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

        <ComparisonMatrix cars={recommendation?.recommended_cars ?? []} />

        {recommendation?.recommended_cars.length ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {recommendation.recommended_cars.map((car) => (
              <RecommendationCard
                key={car.listing_id}
                car={car}
                selected={car.listing_id === selectedCar?.listing_id}
                onSelect={setSelectedRecommendationId}
              />
            ))}
          </div>
        ) : (
          <section className="rounded-md border border-dashed border-line/70 bg-panel p-4 text-sm text-muted">
            {copy.adminCompare.emptyRecommendation}
          </section>
        )}
      </div>
    </div>
  );
}
