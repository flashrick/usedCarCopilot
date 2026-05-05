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
import { defaultMarketForLocale } from "@/lib/market";
import type { RecommendResponse, RetrieveResponse } from "@/lib/types";

const defaultQuery = "I need a reliable car profile under $20,000 for commuting, low running costs, and easy parking.";

export default function HomePage() {
  const { copy, locale } = useLocale();
  const [query, setQuery] = useState(defaultQuery);
  const [budget, setBudget] = useState("20000");
  const [brand, setBrand] = useState("");
  const [bodyType, setBodyType] = useState("");
  const [fuelType, setFuelType] = useState("");
  const [selectedProfileIds, setSelectedProfileIds] = useState<string[]>([]);
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
          market: defaultMarketForLocale(locale),
          query,
          budget_max: maxPrice,
          brands: brand ? [brand] : undefined,
          body_type: bodyType || undefined,
          fuel_type: fuelType || undefined,
          limit: 20,
        };

        const retrieveData = await fetchRetrieve(payload);

        setRetrieval(retrieveData);
        setRecommendation(null);
        setSelectedProfileIds([]);
        setSelectedRecommendationId(null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : copy.adminWorkbench.defaultError);
      }
    });
  }

  function toggleSelection(profileId: string) {
    setError(null);
    setSelectedRecommendationId(null);
    setRecommendation(null);
    setSelectedProfileIds((current) => {
      if (current.includes(profileId)) {
        return current.filter((value) => value !== profileId);
      }
      if (current.length >= 4) {
        setError(copy.adminWorkbench.selectionLimitError);
        return current;
      }
      return [...current, profileId];
    });
  }

  function requestAdvice() {
    if (selectedProfileIds.length < 2) {
      setError(copy.adminWorkbench.selectionMinimumError);
      return;
    }

    setError(null);
    startAdvice(async () => {
      try {
        const recommendData = await fetchRecommend({
          query,
          selected_profile_ids: selectedProfileIds,
        });
        setRecommendation(recommendData);
        setSelectedRecommendationId(recommendData.recommended_profiles[0]?.profile_id ?? null);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : copy.adminWorkbench.defaultError);
      }
    });
  }

  const selectedCar =
    recommendation?.recommended_profiles.find((car) => car.profile_id === selectedRecommendationId) ??
    recommendation?.recommended_profiles[0] ??
    null;

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <QueryComposer
          query={query}
          budget={budget}
          brand={brand}
          bodyType={bodyType}
          fuelType={fuelType}
          onQueryChange={setQuery}
          onBudgetChange={setBudget}
          onBrandChange={setBrand}
          onBodyTypeChange={setBodyType}
          onFuelTypeChange={setFuelType}
          onSubmit={runWorkbenchQuery}
          loading={isRetrieving}
        />

        {error ? (
          <div className="status-danger">
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
                    {copy.adminWorkbench.selectedCount.replace("{count}", String(selectedProfileIds.length))}
                  </div>
                  <button
                    type="button"
                    onClick={requestAdvice}
                    disabled={isAdvising || selectedProfileIds.length < 2}
                    className="btn-primary h-11 rounded-md px-4"
                  >
                    {isAdvising ? copy.adminWorkbench.advising : copy.adminWorkbench.getAdvice}
                  </button>
                </div>
              </div>
              <div className="mt-4">
                <RetrievalTable
                  profiles={retrieval?.vehicle_profiles ?? []}
                  selectedProfileIds={selectedProfileIds}
                  onToggleSelection={toggleSelection}
                />
              </div>
            </section>

            {recommendation?.recommended_profiles.length ? (
              recommendation.recommended_profiles.map((car) => (
                <RecommendationCard
                  key={car.profile_id}
                  car={car}
                  selected={car.profile_id === selectedCar?.profile_id}
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
          <ComparisonMatrix cars={recommendation?.recommended_profiles ?? []} />
        </div>
      </div>
    </div>
  );
}
