"use client";

import Link from "next/link";
import { ArrowRight, BrainCircuit, CheckCircle2, Database, ShieldCheck, Sparkles } from "lucide-react";
import { HomeSearchHero } from "@/components/home/home-search-hero";
import { useLocale } from "@/components/i18n/locale-provider";

export default function HomePage() {
  const { copy } = useLocale();
  const highlightIcons = [Database, ShieldCheck, BrainCircuit] as const;

  return (
    <main className="min-h-screen bg-[#0b1017] text-[#e6eef8]">
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_8%,rgba(0,229,255,0.18),transparent_32%),radial-gradient(circle_at_88%_18%,rgba(123,97,255,0.18),transparent_34%),linear-gradient(180deg,#0b1017_0%,#111a23_100%)]" />
        <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <HomeSearchHero />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
        <div className="grid gap-4 md:grid-cols-3">
          {copy.home.highlights.map(({ title, description }, index) => {
            const Icon = highlightIcons[index];
            return (
            <article key={title} className="rounded-xl border border-white/10 bg-[#131d29] p-5">
              <div className="inline-flex rounded bg-[#00a8ff]/15 p-2 text-[#9adfff]">
                <Icon className="h-5 w-5" />
              </div>
              <h2 className="mt-4 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-[#c5d3e2]">{description}</p>
            </article>
            );
          })}
        </div>
      </section>

      <section className="border-y border-white/10 bg-[#111a24]">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded border border-[#8ae66a]/35 bg-[#8ae66a]/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#c8f8b8]">
              <Sparkles className="h-4 w-4" />
              {copy.home.flowEyebrow}
            </div>
            <h2 className="mt-4 font-[var(--font-space-grotesk)] text-3xl font-semibold text-white">{copy.home.flowTitle}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-[#c5d3e2] md:text-base">
              {copy.home.flowDescription}
            </p>
          </div>

          <div className="rounded-xl border border-white/10 bg-[#151f2a] p-5">
            <ol className="grid gap-3">
              {copy.home.flowSteps.map((item, index) => (
                <li key={item} className="flex items-start gap-3 rounded bg-black/15 p-3 text-sm text-[#d5e1ef]">
                  <span className="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#00a8ff]/20 text-xs font-semibold text-[#a9e5ff]">
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
        <div className="rounded-2xl border border-[#8ae66a]/25 bg-[linear-gradient(120deg,rgba(138,230,106,0.1),rgba(0,168,255,0.1))] p-6 md:p-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="font-[var(--font-space-grotesk)] text-2xl font-semibold text-white">{copy.home.ctaTitle}</h2>
              <div className="mt-3 grid gap-2 text-sm text-[#d5e1ef]">
                {copy.home.ctaPoints.map((point) => (
                  <p key={point} className="inline-flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-[#8ae66a]" /> {point}
                  </p>
                ))}
              </div>
            </div>
            <Link
              href="/find/query"
              className="inline-flex h-12 items-center justify-center gap-2 rounded bg-white px-5 text-sm font-semibold text-[#0f1a24] transition hover:bg-[#dff1ff]"
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
