"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ChevronLeft, Loader2, Search } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { MarketSelector } from "@/components/market/market-selector";
import { fetchRecommend, fetchRetrieve } from "@/lib/api";
import { marketStorageKey, resolveInitialMarket } from "@/lib/market";
import type { RecommendResponse, RetrieveResponse } from "@/lib/types";
import type { Market } from "@/lib/types";
import { SearchResults } from "@/components/search/search-results";

const defaultQuery = "I need a reliable, cheap-to-run car for daily commuting and easy parking.";

export default function FindQueryPage() {
  const [query, setQuery] = useState(defaultQuery);
  const [market, setMarket] = useState<Market>("US");
  const [recommendation, setRecommendation] = useState<RecommendResponse | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [selectedProfileIds, setSelectedProfileIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isAdvising, setIsAdvising] = useState(false);
  const hasLoadedInitialQuery = useRef(false);
  const { copy, locale } = useLocale();

  useEffect(() => {
    if (hasLoadedInitialQuery.current) {
      return;
    }

    hasLoadedInitialQuery.current = true;

    const initialQuery = new URLSearchParams(window.location.search).get("query")?.trim();
    const initialMarket = resolveInitialMarket(locale, new URLSearchParams(window.location.search));
    setMarket(initialMarket);
    if (!initialQuery) {
      return;
    }

    setQuery(initialQuery);
    void runSearch(initialQuery, initialMarket);
  }, [locale]);

  async function runSearch(nextQuery = query, nextMarket = market) {
    const trimmedQuery = nextQuery.trim();
    if (!trimmedQuery) {
      setError(copy.findQuery.emptyQueryError);
      return;
    }

    setError(null);
    setIsSearching(true);

    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(marketStorageKey, nextMarket);
      }
      const retrievePayload = { query: trimmedQuery, market: nextMarket, limit: 20 };

      const retrieveData = await fetchRetrieve(retrievePayload);

      setRetrieval(retrieveData);
      setRecommendation(null);
      setSelectedProfileIds([]);

      document.getElementById("shortlist")?.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : copy.findQuery.searchFailed);
    } finally {
      setIsSearching(false);
    }
  }

  function toggleSelection(profileId: string) {
    setError(null);
    setRecommendation(null);
    setSelectedProfileIds((current) => {
      if (current.includes(profileId)) {
        return current.filter((value) => value !== profileId);
      }
      if (current.length >= 4) {
        setError(copy.findQuery.selectionLimitError);
        return current;
      }
      return [...current, profileId];
    });
  }

  async function requestAdvice() {
    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError(copy.findQuery.emptyQueryError);
      return;
    }
    if (selectedProfileIds.length < 2) {
      setError(copy.findQuery.selectionMinimumError);
      return;
    }

    setError(null);
    setRecommendation(null);
    setIsAdvising(true);
    document.getElementById("advice")?.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const recommendData = await fetchRecommend({
        query: trimmedQuery,
        selected_profile_ids: selectedProfileIds,
      });
      setRecommendation(recommendData);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : copy.findQuery.adviceFailed);
    } finally {
      setIsAdvising(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#0b1017] text-[#e6eef8]">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-5 flex flex-wrap items-center gap-3">
          <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#9cb6d1] hover:text-white">
            <ChevronLeft className="h-4 w-4" />
            {copy.findQuery.backHome}
          </Link>
        </div>

        <section className="rounded-2xl border border-white/10 bg-[#131d29] p-5 md:p-6">
          <h1 className="font-[var(--font-space-grotesk)] text-3xl font-semibold text-white">{copy.findQuery.title}</h1>
          <p className="mt-3 text-sm leading-7 text-[#c5d3e2]">
            {copy.findQuery.description}
          </p>
          <p className="mt-3 text-sm text-[#8fd7ff]">{copy.findQuery.languageHint}</p>

          <div className="mt-4 grid gap-3">
            <MarketSelector market={market} locale={locale} onChange={setMarket} />
            <label className="grid gap-2 text-sm text-[#c5d3e2]">
              {copy.findQuery.textareaLabel}
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={copy.findQuery.textareaPlaceholder}
                className="min-h-28 resize-none rounded border border-white/15 bg-[#0d151f] px-3 py-3 text-white outline-none transition placeholder:text-[#7e91a5] focus:border-[#00a8ff] focus:ring-2 focus:ring-[#00a8ff]/25"
              />
            </label>

            <div className="flex flex-wrap gap-2">
              {copy.findQuery.examplePrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setQuery(prompt)}
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-left text-xs text-[#d6e3f2] transition hover:border-[#00a8ff]/40 hover:bg-[#00a8ff]/10"
                >
                  {prompt}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => void runSearch(query, market)}
              disabled={isSearching}
              className="inline-flex h-12 items-center justify-center gap-2 rounded bg-[#00a8ff] px-5 text-sm font-semibold text-white transition hover:bg-[#2ab7ff] disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              {isSearching ? copy.findQuery.searchingButton : copy.findQuery.searchButton}
            </button>
          </div>

          {error ? (
            <div className="mt-4 flex items-start gap-3 rounded border border-[#ffb4ab]/40 bg-[#93000a]/30 p-3 text-sm text-[#ffdad6]">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : null}
        </section>

        <div className="mt-8 grid gap-8">
          <SearchResults
            recommendation={recommendation}
            retrieval={retrieval}
            selectedProfileIds={selectedProfileIds}
            onToggleSelection={toggleSelection}
            onRequestAdvice={() => void requestAdvice()}
            recommendationLoading={isAdvising}
          />
        </div>
      </div>
    </main>
  );
}
