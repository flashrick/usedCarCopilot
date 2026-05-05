"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, MessageSquareText, Sparkles } from "lucide-react";
import { MarketSelector } from "@/components/market/market-selector";
import { useLocale } from "@/components/i18n/locale-provider";
import { marketStorageKey, resolveInitialMarket } from "@/lib/market";
import type { Market } from "@/lib/types";

export function HomeSearchHero() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [market, setMarket] = useState<Market>("US");
  const { copy, locale } = useLocale();

  useEffect(() => {
    if (typeof window !== "undefined") {
      setMarket(resolveInitialMarket(locale, new URLSearchParams(window.location.search)));
    }
  }, [locale]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      return;
    }

    if (typeof window !== "undefined") {
      window.localStorage.setItem(marketStorageKey, market);
    }
    router.push(`/find/query?market=${encodeURIComponent(market)}&query=${encodeURIComponent(trimmedQuery)}`);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1.02fr_0.98fr] lg:items-end">
      <div className="max-w-3xl">
        <div className="badge-secondary">
          <Sparkles className="h-4 w-4" />
          {copy.home.badge}
        </div>
        <h1 className="mt-6 font-[var(--font-space-grotesk)] text-4xl font-bold leading-tight text-textStrong md:text-6xl">
          {copy.home.title}
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-textBody md:text-lg">
          {copy.home.description}
        </p>
        <p className="mt-4 text-sm text-secondaryDeep">{copy.home.languageHint}</p>
        <div className="mt-6 grid gap-3 text-sm text-textBody sm:grid-cols-3">
          {copy.home.cards.map((card) => (
            <div key={card} className="rounded-2xl border border-line/80 bg-white/80 p-4 shadow-panel">
              {card}
            </div>
          ))}
        </div>
      </div>

      <div className="surface-card-hero p-5 md:p-6">
        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-textStrong">{copy.home.panelTitle}</div>
              <p className="mt-1 text-sm leading-6 text-textBody">
                {copy.home.panelDescription}
              </p>
            </div>
            <span className="inline-flex rounded-2xl bg-primarySoft p-3 text-primary">
              <MessageSquareText className="h-5 w-5" />
            </span>
          </div>

          <label className="grid gap-2 text-sm text-textBody">
            {copy.home.textareaLabel}
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={copy.home.textareaPlaceholder}
              className="theme-textarea min-h-40 resize-none placeholder:text-mutedSoft"
            />
          </label>

          <MarketSelector market={market} locale={locale} onChange={setMarket} />

          <div className="flex flex-wrap gap-2">
            {copy.home.examplePrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => setQuery(prompt)}
                className="chip-muted text-left"
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={!query.trim()}
              className="btn-primary h-12"
            >
              {copy.home.searchButton}
              <ArrowRight className="h-4 w-4" />
            </button>
            <Link
              href={`/find/query?market=${encodeURIComponent(market)}`}
              className="btn-secondary h-12"
            >
              {copy.home.workspaceButton}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
