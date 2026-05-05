"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { useParams, useRouter } from "next/navigation";
import { ChevronLeft, History as HistoryIcon } from "lucide-react";
import { RecommendationHistoryView } from "@/components/history/recommendation-history-view";
import { useLocale } from "@/components/i18n/locale-provider";
import { ApiError, fetchHistoryDetail } from "@/lib/api";
import { formatTemplate } from "@/lib/i18n";
import { marketLabel } from "@/lib/market";
import type { HistoryDetail } from "@/lib/types";

export default function HistoryDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { copy, locale } = useLocale();
  const [detail, setDetail] = useState<HistoryDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const response = await fetchHistoryDetail(params.id);
        setDetail(response);
      } catch (caughtError) {
        if (caughtError instanceof ApiError && caughtError.status === 401) {
          router.replace(`/login?next=${encodeURIComponent(`/history/${params.id}`)}` as Route);
          return;
        }
        if (caughtError instanceof ApiError && caughtError.status === 404) {
          setError(copy.history.missing);
          return;
        }
        setError(caughtError instanceof Error ? caughtError.message : copy.history.loadFailed);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [copy.history.loadFailed, copy.history.missing, params.id, router]);

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div className="mb-5 flex flex-wrap items-center gap-3">
          <Link href="/history" className="inline-flex items-center gap-2 text-sm text-muted transition hover:text-primaryDeep">
            <ChevronLeft className="h-4 w-4" />
            {copy.history.backToHistory}
          </Link>
        </div>

        {loading ? <div className="rounded-xl bg-shell px-4 py-3 text-sm text-muted">{copy.siteNav.loading}</div> : null}
        {error ? <div className="status-danger">{error}</div> : null}

        {detail ? (
          <div className="grid gap-6">
            <section className="surface-card p-5 md:p-6">
              <div className="flex items-start gap-3">
                <span className="inline-flex rounded-xl bg-primarySoft p-2 text-primary">
                  <HistoryIcon className="h-5 w-5" />
                </span>
                <div className="min-w-0">
                  <h1 className="font-[var(--font-space-grotesk)] text-3xl font-semibold text-textStrong">{copy.history.detailTitle}</h1>
                  <p className="mt-3 max-w-4xl text-sm leading-7 text-textBody">{copy.history.detailDescription}</p>
                  <div className="mt-4 grid gap-2 text-sm text-textBody">
                    <p><span className="font-semibold text-textStrong">{copy.history.sourceQuery}:</span> {detail.query}</p>
                    <p><span className="font-semibold text-textStrong">{copy.history.sourceMarket}:</span> {marketLabel(detail.market, locale)}</p>
                    <p><span className="font-semibold text-textStrong">{copy.history.createdAt}:</span> {new Date(detail.created_at).toLocaleString()}</p>
                    <p>
                      <span className="font-semibold text-textStrong">{copy.history.sourceSelection}:</span>{" "}
                      {formatTemplate(copy.history.selectedCount, { count: detail.selected_profile_ids.length })}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <RecommendationHistoryView recommendation={detail.recommend_response} />
          </div>
        ) : null}
      </div>
    </main>
  );
}
