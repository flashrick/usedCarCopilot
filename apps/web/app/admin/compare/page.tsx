"use client";

import { useEffect, useState } from "react";
import { useLocale } from "@/components/i18n/locale-provider";
import { ComparisonMatrix } from "@/components/workbench/comparison-matrix";
import { fetchRecommend } from "@/lib/api";
import type { RecommendResponse } from "@/lib/types";

export default function ComparePage() {
  const { copy } = useLocale();
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    try {
      const response = await fetchRecommend({
        query: "Which of these is better for city driving: Toyota Aqua, Honda Fit, or Mazda2?",
        location: "Auckland",
        limit: 3,
      });
      setData(response);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : copy.adminCompare.defaultError);
    }
  }

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.adminCompare.eyebrow}</div>
          <h2 className="mt-1 text-2xl font-semibold">{copy.adminCompare.title}</h2>
          <p className="mt-2 max-w-3xl text-sm text-muted">{copy.adminCompare.description}</p>
          {error ? <div className="mt-3 text-sm text-rose-700">{error}</div> : null}
        </section>

        <ComparisonMatrix cars={data?.recommended_cars ?? []} />
      </div>
    </div>
  );
}
