"use client";

import { Search, SlidersHorizontal } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { formatTemplate, translateValue } from "@/lib/i18n";

type QueryComposerProps = {
  query: string;
  budget: string;
  brand: string;
  bodyType: string;
  fuelType: string;
  onQueryChange: (value: string) => void;
  onBudgetChange: (value: string) => void;
  onBrandChange: (value: string) => void;
  onBodyTypeChange: (value: string) => void;
  onFuelTypeChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
};

const brands = ["", "Toyota", "Honda", "Mazda"];
const bodyTypes = ["", "hatchback", "sedan", "suv"];
const fuelTypes = ["", "petrol", "hybrid"];

export function QueryComposer(props: QueryComposerProps) {
  const { copy, locale } = useLocale();
  const {
    query,
    budget,
    brand,
    bodyType,
    fuelType,
    onQueryChange,
    onBudgetChange,
    onBrandChange,
    onBodyTypeChange,
    onFuelTypeChange,
    onSubmit,
    loading,
  } = props;

  return (
    <section className="surface-card overflow-hidden">
      <div className="border-b border-line/70 bg-[linear-gradient(135deg,rgba(219,234,254,0.72),rgba(255,237,213,0.55))] px-4 py-4">
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="section-eyebrow">{copy.queryComposer.eyebrow}</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight">{copy.queryComposer.title}</h2>
            </div>
            <div className="hidden rounded-xl border border-line/70 bg-white/80 px-3 py-2 text-xs text-muted md:flex md:items-center md:gap-2">
              <SlidersHorizontal className="h-4 w-4" />
              {copy.queryComposer.helper}
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.7fr)_repeat(4,minmax(0,0.55fr))_auto]">
            <label className="grid gap-1">
              <span className="text-xs font-medium text-muted">{copy.queryComposer.need}</span>
              <textarea
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                className="theme-textarea min-h-24 px-3 py-3"
                placeholder={copy.queryComposer.placeholder}
              />
            </label>

            <Field label={copy.queryComposer.budget} value={budget} onChange={onBudgetChange} placeholder="12000" />
            <SelectField
              label={copy.queryComposer.brand}
              value={brand}
              onChange={onBrandChange}
              options={brands}
              localeLabel={(option) =>
                option ? translateValue(option, locale) : formatTemplate(copy.queryComposer.allLabel, { label: copy.queryComposer.brand })
              }
            />
            <SelectField
              label={copy.queryComposer.body}
              value={bodyType}
              onChange={onBodyTypeChange}
              options={bodyTypes}
              localeLabel={(option) =>
                option ? translateValue(option, locale) : formatTemplate(copy.queryComposer.allLabel, { label: copy.queryComposer.body })
              }
            />
            <SelectField
              label={copy.queryComposer.fuel}
              value={fuelType}
              onChange={onFuelTypeChange}
              options={fuelTypes}
              localeLabel={(option) =>
                option ? translateValue(option, locale) : formatTemplate(copy.queryComposer.allLabel, { label: copy.queryComposer.fuel })
              }
            />

            <button
              type="button"
              onClick={onSubmit}
              className="btn-primary mt-[25px] h-11 rounded-xl px-4"
              disabled={loading}
            >
              <Search className="h-4 w-4" />
              {loading ? copy.queryComposer.running : copy.queryComposer.retrieve}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function Field({
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
    <label className="grid gap-1">
      <span className="text-xs font-medium text-muted">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="theme-input"
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
    <label className="grid gap-1">
      <span className="text-xs font-medium text-muted">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="theme-select"
      >
        {options.map((option) => (
          <option key={option || "all"} value={option}>
            {localeLabel(option)}
          </option>
        ))}
      </select>
    </label>
  );
}
