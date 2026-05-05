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
        <div className="inline-flex items-center gap-2 rounded-full border border-[#61dafb]/30 bg-[#61dafb]/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-[#bdefff]">
          <Sparkles className="h-4 w-4" />
          {copy.home.badge}
        </div>
        <h1 className="mt-6 font-[var(--font-space-grotesk)] text-4xl font-bold leading-tight text-white md:text-6xl">
          {copy.home.title}
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-[#c5d3e2] md:text-lg">
          {copy.home.description}
        </p>
        <p className="mt-4 text-sm text-[#8fd7ff]">{copy.home.languageHint}</p>
        <div className="mt-6 grid gap-3 text-sm text-[#d7e3ef] sm:grid-cols-3">
          {copy.home.cards.map((card) => (
            <div key={card} className="rounded-xl border border-white/10 bg-white/5 p-4">
              {card}
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-[28px] border border-white/10 bg-[linear-gradient(180deg,rgba(19,29,41,0.96),rgba(11,16,23,0.98))] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.35)] md:p-6">
        <form onSubmit={handleSubmit} className="grid gap-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-[#dce9f6]">{copy.home.panelTitle}</div>
              <p className="mt-1 text-sm leading-6 text-[#9fb4c9]">
                {copy.home.panelDescription}
              </p>
            </div>
            <span className="inline-flex rounded-2xl bg-[#00a8ff]/15 p-3 text-[#9adfff]">
              <MessageSquareText className="h-5 w-5" />
            </span>
          </div>

          <label className="grid gap-2 text-sm text-[#c5d3e2]">
            {copy.home.textareaLabel}
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={copy.home.textareaPlaceholder}
              className="min-h-40 resize-none rounded-2xl border border-white/15 bg-[#0d151f] px-4 py-4 text-white outline-none transition placeholder:text-[#7e91a5] focus:border-[#00a8ff] focus:ring-2 focus:ring-[#00a8ff]/25"
            />
          </label>

          <MarketSelector market={market} locale={locale} onChange={setMarket} />

          <div className="flex flex-wrap gap-2">
            {copy.home.examplePrompts.map((prompt) => (
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

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={!query.trim()}
              className="inline-flex h-12 items-center gap-2 rounded bg-[#00a8ff] px-5 text-sm font-semibold text-white transition hover:bg-[#2ab7ff] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {copy.home.searchButton}
              <ArrowRight className="h-4 w-4" />
            </button>
            <Link
              href={`/find/query?market=${encodeURIComponent(market)}`}
              className="inline-flex h-12 items-center rounded border border-white/20 px-5 text-sm font-semibold text-[#d6e3f2] transition hover:bg-white/10"
            >
              {copy.home.workspaceButton}
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
