"use client";

import { Search, SlidersHorizontal } from "lucide-react";

type QueryComposerProps = {
  query: string;
  budget: string;
  brand: string;
  bodyType: string;
  location: string;
  onQueryChange: (value: string) => void;
  onBudgetChange: (value: string) => void;
  onBrandChange: (value: string) => void;
  onBodyTypeChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  onSubmit: () => void;
  loading?: boolean;
};

const brands = ["", "Toyota", "Honda", "Mazda"];
const bodyTypes = ["", "hatchback", "sedan", "suv"];

export function QueryComposer(props: QueryComposerProps) {
  const {
    query,
    budget,
    brand,
    bodyType,
    location,
    onQueryChange,
    onBudgetChange,
    onBrandChange,
    onBodyTypeChange,
    onLocationChange,
    onSubmit,
    loading,
  } = props;

  return (
    <section className="rounded-md bg-gradient-to-r from-steelDeep via-steel to-[#557893] p-[1px] shadow-panel">
      <div className="rounded-[5px] bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(246,248,250,0.98))] px-4 py-4">
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-muted">Decision Workbench</p>
              <h2 className="mt-1 text-2xl font-semibold tracking-tight">Shortlist candidates with evidence, risks, and retrieval context.</h2>
            </div>
            <div className="hidden rounded-md bg-shell px-3 py-2 text-xs text-muted md:flex md:items-center md:gap-2">
              <SlidersHorizontal className="h-4 w-4" />
              Citation-forward analyst view
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.7fr)_repeat(4,minmax(0,0.55fr))_auto]">
            <label className="grid gap-1">
              <span className="text-xs font-medium text-muted">Need</span>
              <textarea
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                className="min-h-24 rounded-md border border-line bg-white px-3 py-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
                placeholder="I need a reliable car under $12,000 for commuting in Auckland."
              />
            </label>

            <Field label="Budget" value={budget} onChange={onBudgetChange} placeholder="12000" />
            <SelectField label="Brand" value={brand} onChange={onBrandChange} options={brands} />
            <SelectField label="Body" value={bodyType} onChange={onBodyTypeChange} options={bodyTypes} />
            <Field label="Location" value={location} onChange={onLocationChange} placeholder="Auckland" />

            <button
              type="button"
              onClick={onSubmit}
              className="mt-[25px] flex h-11 items-center justify-center gap-2 rounded-md bg-gradient-to-b from-steel to-steelDeep px-4 text-sm font-medium text-white shadow-panel transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={loading}
            >
              <Search className="h-4 w-4" />
              {loading ? "Running..." : "Recommend"}
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
        className="h-11 rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
      />
    </label>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="grid gap-1">
      <span className="text-xs font-medium text-muted">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-11 rounded-md border border-line bg-white px-3 text-sm outline-none transition focus:border-steel focus:ring-2 focus:ring-steel/20"
      >
        {options.map((option) => (
          <option key={option || "all"} value={option}>
            {option || `All ${label}`}
          </option>
        ))}
      </select>
    </label>
  );
}
