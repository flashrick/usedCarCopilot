"use client";

import { useEffect, useState, useTransition } from "react";
import { AlertTriangle } from "lucide-react";
import { QueryComposer } from "@/components/workbench/query-composer";
import { RecommendationCard } from "@/components/workbench/recommendation-card";
import { EvidencePanel } from "@/components/workbench/evidence-panel";
import { DebugPanel } from "@/components/workbench/debug-panel";
import { ComparisonMatrix } from "@/components/workbench/comparison-matrix";
import { RetrievalTable } from "@/components/workbench/retrieval-table";
import { fetchRecommend, fetchRetrieve } from "@/lib/api";
import type { RecommendResponse, RetrieveResponse } from "@/lib/types";

const defaultQuery = "I need a reliable car under $12,000 for commuting in Auckland.";

export default function HomePage() {
  const [query, setQuery] = useState(defaultQuery);
  const [budget, setBudget] = useState("12000");
  const [brand, setBrand] = useState("");
  const [bodyType, setBodyType] = useState("");
  const [location, setLocation] = useState("Auckland");
  const [selectedListingId, setSelectedListingId] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    runWorkbenchQuery();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function runWorkbenchQuery() {
    setError(null);
    startTransition(async () => {
      try {
        const payload = {
          query,
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
        setSelectedListingId(recommendData.recommended_cars[0]?.listing_id ?? null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Unknown frontend error");
      }
    });
  }

  const selectedCar =
    recommendation?.recommended_cars.find((car) => car.listing_id === selectedListingId) ??
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
          loading={isPending}
        />

        {error ? (
          <div className="flex items-center gap-3 rounded-md border border-riskHigh/70 bg-[#fff1f1] px-4 py-3 text-sm text-rose-900">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-[1.45fr_0.78fr]">
          <section className="grid gap-4">
            {recommendation?.recommended_cars.map((car) => (
              <RecommendationCard
                key={car.listing_id}
                car={car}
                selected={car.listing_id === selectedCar?.listing_id}
                onSelect={setSelectedListingId}
              />
            ))}
          </section>

          <section className="grid gap-4">
            <EvidencePanel evidence={recommendation?.evidence ?? []} highlightedIds={selectedCar?.evidence_ids ?? []} />
            <DebugPanel debug={recommendation?.debug ?? { state: "Run a query to inspect provider path." }} />
          </section>
        </div>

        <div className="grid gap-4">
          <ComparisonMatrix cars={recommendation?.recommended_cars ?? []} />
          <RetrievalTable listings={retrieval?.listings ?? []} />
        </div>
      </div>
    </div>
  );
}
