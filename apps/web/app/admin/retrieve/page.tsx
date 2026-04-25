"use client";

import { useState, useTransition } from "react";
import { fetchRetrieve } from "@/lib/api";
import type { RetrieveResponse } from "@/lib/types";
import { RetrieveResults } from "@/components/retrieve/retrieve-results";

export default function RetrievePage() {
  const [query, setQuery] = useState("I want a hatchback that is cheap to run and easy to park in Auckland.");
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrieveResponse | null>(null);

  function runRetrieve() {
    setError(null);
    startTransition(async () => {
      try {
        const response = await fetchRetrieve({ query, location: "Auckland", limit: 8 });
        setData(response);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : "Unknown retrieval error");
      }
    });
  }

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">Retrieval Explorer</div>
          <h2 className="mt-1 text-2xl font-semibold">Inspect listings, knowledge sources, and semantic chunks.</h2>
          <div className="mt-4 flex flex-col gap-3 lg:flex-row">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="min-h-24 flex-1 rounded-md border border-line bg-shell px-3 py-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
            />
            <button
              type="button"
              onClick={runRetrieve}
              className="h-11 rounded-md bg-gradient-to-b from-steel to-steelDeep px-4 text-sm font-medium text-white shadow-panel transition hover:brightness-105 disabled:opacity-70"
              disabled={isPending}
            >
              {isPending ? "Running..." : "Retrieve"}
            </button>
          </div>
          {error ? <div className="mt-3 text-sm text-rose-700">{error}</div> : null}
        </section>

        <RetrieveResults data={data} />
      </div>
    </div>
  );
}
