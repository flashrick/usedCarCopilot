"use client";

import { useState, useTransition } from "react";
import { useLocale } from "@/components/i18n/locale-provider";
import { fetchRetrieve } from "@/lib/api";
import { defaultMarketForLocale } from "@/lib/market";
import type { RetrieveResponse } from "@/lib/types";
import { RetrieveResults } from "@/components/retrieve/retrieve-results";

export default function RetrievePage() {
  const { copy, locale } = useLocale();
  const [query, setQuery] = useState("I want a hatchback profile that is cheap to run, easy to park, and comfortable enough for commuting.");
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RetrieveResponse | null>(null);

  function runRetrieve() {
    setError(null);
    startTransition(async () => {
      try {
        const response = await fetchRetrieve({ query, market: defaultMarketForLocale(locale), limit: 8 });
        setData(response);
      } catch (caughtError) {
        setError(caughtError instanceof Error ? caughtError.message : copy.retrievePage.defaultError);
      }
    });
  }

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.retrievePage.eyebrow}</div>
          <h2 className="mt-1 text-2xl font-semibold">{copy.retrievePage.title}</h2>
          <div className="mt-4 flex flex-col gap-3 lg:flex-row">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="theme-textarea min-h-24 flex-1 rounded-md px-3 py-3"
            />
            <button
              type="button"
              onClick={runRetrieve}
              className="btn-primary h-11 rounded-md px-4"
              disabled={isPending}
            >
              {isPending ? copy.retrievePage.running : copy.retrievePage.retrieve}
            </button>
          </div>
          {error ? <div className="status-danger mt-3">{error}</div> : null}
        </section>

        <RetrieveResults data={data} />
      </div>
    </div>
  );
}
