"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { ArrowRight, Clock3, History as HistoryIcon } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { fetchHistoryList, ApiError } from "@/lib/api";
import { formatTemplate } from "@/lib/i18n";
import { marketLabel } from "@/lib/market";
import type { HistoryListItem } from "@/lib/types";

export default function HistoryPage() {
  const router = useRouter();
  const { copy, locale } = useLocale();
  const [items, setItems] = useState<HistoryListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const response = await fetchHistoryList();
        setItems(response);
      } catch (caughtError) {
        if (caughtError instanceof ApiError && caughtError.status === 401) {
          router.replace(`/login?next=${encodeURIComponent("/history")}` as Route);
          return;
        }
        setError(caughtError instanceof Error ? caughtError.message : copy.history.loadFailed);
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [copy.history.loadFailed, router]);

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <section className="border-b border-line/70 pb-6">
          <div className="flex items-start gap-3">
            <span className="inline-flex rounded-xl bg-primarySoft p-2 text-primary">
              <HistoryIcon className="h-5 w-5" />
            </span>
            <div>
              <h1 className="font-[var(--font-space-grotesk)] text-3xl font-semibold text-textStrong">{copy.history.title}</h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-textBody">{copy.history.description}</p>
            </div>
          </div>
        </section>

        {loading ? <div className="mt-6 rounded-xl bg-shell px-4 py-3 text-sm text-muted">{copy.siteNav.loading}</div> : null}
        {error ? <div className="status-danger mt-6">{error}</div> : null}
        {!loading && !error && items.length === 0 ? <div className="surface-card mt-6 p-6 text-sm text-textBody">{copy.history.empty}</div> : null}

        <div className="mt-6 grid gap-4">
          {items.map((item) => (
            <article key={item.id} className="surface-card p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                    <span className="badge-secondary">{marketLabel(item.market, locale)}</span>
                    <span className="inline-flex items-center gap-1">
                      <Clock3 className="h-3.5 w-3.5" />
                      {copy.history.createdAt}: {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>
                  <h2 className="mt-3 text-xl font-semibold text-textStrong">{item.recommended_title ?? item.query}</h2>
                  <p className="mt-2 text-sm leading-6 text-textBody">{item.query}</p>
                  <p className="mt-3 text-xs text-muted">
                    {formatTemplate(copy.history.selectedCount, { count: item.selected_profile_ids.length })} · {item.recommended_profile_count}
                  </p>
                </div>
                <Link href={`/history/${item.id}`} className="btn-primary h-11 shrink-0">
                  {copy.history.openDetail}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </article>
          ))}
        </div>
      </div>
    </main>
  );
}
