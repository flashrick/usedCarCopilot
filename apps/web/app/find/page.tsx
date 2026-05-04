"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, ChevronLeft, SlidersHorizontal } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { formatTemplate, translateValue } from "@/lib/i18n";
import { defaultFindFilters, findSelectOptions, readFindFilters, toFindSearchParams, type FindFilters } from "@/lib/find-flow";

export default function FindSetupPage() {
  const router = useRouter();
  const [filters, setFilters] = useState<FindFilters>(defaultFindFilters);
  const { copy, locale } = useLocale();

  useEffect(() => {
    setFilters(readFindFilters(new URLSearchParams(window.location.search)));
  }, []);

  function updateField<K extends keyof FindFilters>(key: K, value: FindFilters[K]) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function continueToQuery() {
    const params = toFindSearchParams(filters);
    const queryString = params.toString();
    router.push(queryString ? `/find/query?${queryString}` : "/find/query");
  }

  return (
    <main className="min-h-screen bg-[#0b1017] text-[#e6eef8]">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div className="mb-6 flex items-center justify-between gap-3">
          <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#9cb6d1] hover:text-white">
            <ChevronLeft className="h-4 w-4" />
            {copy.findSetup.backHome}
          </Link>
          <span className="rounded border border-white/15 bg-white/5 px-3 py-1 text-xs tracking-[0.16em] text-[#b6cae0]">
            {copy.findSetup.stepLabel}
          </span>
        </div>

        <section className="rounded-2xl border border-white/10 bg-[#131d29] p-5 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="font-[var(--font-space-grotesk)] text-3xl font-semibold text-white">{copy.findSetup.title}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-[#c5d3e2]">
                {copy.findSetup.description}
              </p>
            </div>
            <span className="inline-flex rounded bg-[#00a8ff]/15 p-2 text-[#9adfff]">
              <SlidersHorizontal className="h-5 w-5" />
            </span>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <InputField
              label={copy.findSetup.budget}
              value={filters.budget}
              onChange={(value) => updateField("budget", value)}
              placeholder="12000"
            />
            <InputField
              label={copy.findSetup.location}
              value={filters.location}
              onChange={(value) => updateField("location", value)}
              placeholder="Auckland"
            />

            <SelectField
              label={copy.findSetup.brand}
              value={filters.brand}
              onChange={(value) => updateField("brand", value)}
              options={findSelectOptions.brand}
              localeLabel={(option) =>
                option ? translateValue(option, locale) : formatTemplate(copy.findSetup.anyOption, { label: copy.findSetup.brand })
              }
            />
            <SelectField
              label={copy.findSetup.bodyType}
              value={filters.bodyType}
              onChange={(value) => updateField("bodyType", value)}
              options={findSelectOptions.bodyType}
              localeLabel={(option) =>
                option ? translateValue(option, locale) : formatTemplate(copy.findSetup.anyOption, { label: copy.findSetup.bodyType })
              }
            />

            <SelectField
              label={copy.findSetup.fuelType}
              value={filters.fuel}
              onChange={(value) => updateField("fuel", value)}
              options={findSelectOptions.fuel}
              localeLabel={(option) =>
                option ? translateValue(option, locale) : formatTemplate(copy.findSetup.anyOption, { label: copy.findSetup.fuelType })
              }
            />
            <InputField
              label={copy.findSetup.maxMileage}
              value={filters.mileage}
              onChange={(value) => updateField("mileage", value)}
              placeholder="90000"
            />
          </div>

          <p className="mt-4 text-xs text-[#9cb6d1]">{copy.findSetup.numericHint}</p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={continueToQuery}
              className="inline-flex h-11 items-center gap-2 rounded bg-[#00a8ff] px-5 text-sm font-semibold text-white transition hover:bg-[#2ab7ff]"
            >
              {copy.findSetup.continueButton}
              <ArrowRight className="h-4 w-4" />
            </button>
            <Link
              href="/find/query"
              className="inline-flex h-11 items-center rounded border border-white/20 px-5 text-sm font-semibold text-[#d2dfed] transition hover:bg-white/10"
            >
              {copy.findSetup.skipButton}
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}

function InputField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="grid gap-2 text-sm text-[#c5d3e2]">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="h-11 rounded border border-white/15 bg-[#0d151f] px-3 text-white outline-none transition placeholder:text-[#7e91a5] focus:border-[#00a8ff] focus:ring-2 focus:ring-[#00a8ff]/25"
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  localeLabel,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  localeLabel: (value: string) => string;
}) {
  return (
    <label className="grid gap-2 text-sm text-[#c5d3e2]">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 rounded border border-white/15 bg-[#0d151f] px-3 text-white outline-none transition focus:border-[#00a8ff] focus:ring-2 focus:ring-[#00a8ff]/25"
      >
        {options.map((option) => (
          <option key={option || "any"} value={option}>
            {localeLabel(option)}
          </option>
        ))}
      </select>
    </label>
  );
}
