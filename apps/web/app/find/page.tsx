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
    <main className="min-h-screen bg-canvas text-ink">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <div className="mb-6 flex items-center justify-between gap-3">
          <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted transition hover:text-primaryDeep">
            <ChevronLeft className="h-4 w-4" />
            {copy.findSetup.backHome}
          </Link>
          <span className="badge-secondary">
            {copy.findSetup.stepLabel}
          </span>
        </div>

        <section className="surface-card p-5 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="font-[var(--font-space-grotesk)] text-3xl font-semibold text-textStrong">{copy.findSetup.title}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-textBody">
                {copy.findSetup.description}
              </p>
            </div>
            <span className="inline-flex rounded-xl bg-primarySoft p-2 text-primary">
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
          </div>

          <p className="mt-4 text-xs text-secondaryDeep">{copy.findSetup.numericHint}</p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={continueToQuery}
              className="btn-primary h-11"
            >
              {copy.findSetup.continueButton}
              <ArrowRight className="h-4 w-4" />
            </button>
            <Link
              href="/find/query"
              className="btn-secondary h-11"
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
    <label className="grid gap-2 text-sm text-textBody">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="theme-input placeholder:text-mutedSoft"
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
    <label className="grid gap-2 text-sm text-textBody">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="theme-select"
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
