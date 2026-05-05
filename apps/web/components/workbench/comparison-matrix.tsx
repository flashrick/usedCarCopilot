"use client";

import { useLocale } from "@/components/i18n/locale-provider";
import { formatTemplate } from "@/lib/i18n";
import type { RecommendedProfile } from "@/lib/types";

type ComparisonField =
  | "match_score"
  | "powertrain_summary"
  | "why_it_matches"
  | "trade_offs"
  | "risk_flags"
  | "valuation_summary"
  | "next_steps";

export function ComparisonMatrix({ cars }: { cars: RecommendedProfile[] }) {
  const { copy } = useLocale();
  const rows: Array<{ label: string; field: ComparisonField }> = [
    { label: copy.comparisonMatrix.rows.match, field: "match_score" },
    { label: copy.comparisonMatrix.rows.powertrain, field: "powertrain_summary" },
    { label: copy.comparisonMatrix.rows.why, field: "why_it_matches" },
    { label: copy.comparisonMatrix.rows.tradeOffs, field: "trade_offs" },
    { label: copy.comparisonMatrix.rows.riskFlags, field: "risk_flags" },
    { label: copy.comparisonMatrix.rows.valuation, field: "valuation_summary" },
    { label: copy.comparisonMatrix.rows.nextSteps, field: "next_steps" },
  ];

  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.comparisonMatrix.eyebrow}</div>
          <h3 className="mt-1 text-lg font-semibold">{copy.comparisonMatrix.title}</h3>
        </div>
        <div className="rounded-md bg-shell px-3 py-2 text-xs text-muted">
          {formatTemplate(copy.comparisonMatrix.topShortlisted, { count: cars.length })}
        </div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className="w-40 rounded-l-md bg-shell px-4 py-3 text-left text-xs uppercase tracking-[0.18em] text-muted">{copy.comparisonMatrix.dimension}</th>
              {cars.map((car, index) => (
                <th
                  key={car.profile_id}
                  className={`min-w-64 bg-shell px-4 py-3 text-left font-medium ${index === cars.length - 1 ? "rounded-r-md" : ""}`}
                >
                  {car.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <td className="border-b border-line/60 px-4 py-4 align-top text-xs font-medium uppercase tracking-[0.16em] text-muted">
                  {row.label}
                </td>
                {cars.map((car) => (
                  <td key={`${car.profile_id}-${row.field}`} className="border-b border-line/60 px-4 py-4 align-top">
                    {renderCell(car, row.field)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function renderCell(car: RecommendedProfile, field: ComparisonField) {
  if (field === "match_score") {
    return <div className="text-lg font-semibold text-primaryDeep">{car.match_score}</div>;
  }

  if (field === "risk_flags") {
    return (
      <div className="flex flex-wrap gap-2">
        {car.risk_flags.map((flag) => (
          <span key={`${car.profile_id}-${flag.label}`} className="rounded-md bg-shell px-2 py-1 text-xs text-muted">
            {flag.label}
          </span>
        ))}
      </div>
    );
  }

  const values = car[field];
  if (Array.isArray(values)) {
    return (
      <div className="space-y-2">
        {values.map((value) => (
          <div key={`${car.profile_id}-${String(value)}`} className="rounded-md bg-shell px-3 py-2 text-xs text-muted">
            {String(value)}
          </div>
        ))}
      </div>
    );
  }

  return <div className="text-xs text-muted">{String(values)}</div>;
}
