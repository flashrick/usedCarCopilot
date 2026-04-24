"use client";

import { useEffect, useState } from "react";
import { ComparisonMatrix } from "@/components/workbench/comparison-matrix";
import { fetchRecommend } from "@/lib/api";
import type { RecommendResponse } from "@/lib/types";

export default function ComparePage() {
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
      setError(caughtError instanceof Error ? caughtError.message : "Unknown comparison error");
    }
  }

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">Comparison View</div>
          <h2 className="mt-1 text-2xl font-semibold">Read trade-offs without leaving the shortlist.</h2>
          <p className="mt-2 max-w-3xl text-sm text-muted">
            This view is fed by the same recommendation contract as the main workbench, but optimized for side-by-side
            decision-making.
          </p>
          {error ? <div className="mt-3 text-sm text-rose-700">{error}</div> : null}
        </section>

        <ComparisonMatrix cars={data?.recommended_cars ?? []} />
      </div>
    </div>
  );
}
