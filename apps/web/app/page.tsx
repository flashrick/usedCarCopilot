"use client";

import Link from "next/link";
import { ArrowRight, BrainCircuit, CheckCircle2, Database, ShieldCheck, Sparkles } from "lucide-react";
import { HomeSearchHero } from "@/components/home/home-search-hero";
import { useLocale } from "@/components/i18n/locale-provider";

export default function HomePage() {
  const { copy } = useLocale();
  const highlightIcons = [Database, ShieldCheck, BrainCircuit] as const;

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <section className="relative overflow-hidden border-b border-line/70">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_8%,rgba(37,99,235,0.12),transparent_32%),radial-gradient(circle_at_88%_18%,rgba(6,182,212,0.1),transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.96)_0%,rgba(248,250,252,0.98)_100%)]" />
        <div className="absolute inset-0 bg-header-grid bg-[size:28px_28px] opacity-50" />
        <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <HomeSearchHero />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
        <div className="grid gap-4 md:grid-cols-3">
          {copy.home.highlights.map(({ title, description }, index) => {
            const Icon = highlightIcons[index];
            return (
              <article key={title} className="surface-card p-5">
                <div className="inline-flex rounded-xl bg-secondarySoft p-2 text-secondaryDeep">
                  <Icon className="h-5 w-5" />
                </div>
                <h2 className="mt-4 font-[var(--font-space-grotesk)] text-xl font-semibold text-textStrong">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-textBody">{description}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="border-y border-line/70 bg-white/70">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
          <div>
            <div className="badge-accent">
              <Sparkles className="h-4 w-4" />
              {copy.home.flowEyebrow}
            </div>
            <h2 className="mt-4 font-[var(--font-space-grotesk)] text-3xl font-semibold text-textStrong">{copy.home.flowTitle}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-textBody md:text-base">
              {copy.home.flowDescription}
            </p>
          </div>

          <div className="surface-card-muted p-5">
            <ol className="grid gap-3">
              {copy.home.flowSteps.map((item, index) => (
                <li key={item} className="flex items-start gap-3 rounded-2xl border border-line/70 bg-white/80 p-3 text-sm text-textBody">
                  <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primarySoft text-xs font-semibold text-primaryDeep">
                    {index + 1}
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 lg:py-16">
        <div className="rounded-[28px] border border-line/70 bg-[linear-gradient(120deg,rgba(255,237,213,0.72),rgba(219,234,254,0.66),rgba(207,250,254,0.46))] p-6 shadow-panel md:p-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="font-[var(--font-space-grotesk)] text-2xl font-semibold text-textStrong">{copy.home.ctaTitle}</h2>
              <div className="mt-3 grid gap-2 text-sm text-textBody">
                {copy.home.ctaPoints.map((point) => (
                  <p key={point} className="inline-flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-accent" /> {point}
                  </p>
                ))}
              </div>
            </div>
            <Link
              href="/find/query"
              className="btn-primary h-12"
            >
              {copy.home.ctaButton}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
