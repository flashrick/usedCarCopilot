"use client";

import type { RecommendedCar } from "@/lib/types";

const rows = [
  { label: "Match", field: "match_score" },
  { label: "Why", field: "why_it_matches" },
  { label: "Risk flags", field: "risk_flags" },
  { label: "Next steps", field: "next_steps" },
];

export function ComparisonMatrix({ cars }: { cars: RecommendedCar[] }) {
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">Comparison</div>
          <h3 className="mt-1 text-lg font-semibold">Selected vehicle matrix</h3>
        </div>
        <div className="rounded-md bg-shell px-3 py-2 text-xs text-muted">Top {cars.length} shortlisted vehicles</div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className="w-40 rounded-l-md bg-shell px-4 py-3 text-left text-xs uppercase tracking-[0.18em] text-muted">Dimension</th>
              {cars.map((car, index) => (
                <th
                  key={car.listing_id}
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
                  <td key={`${car.listing_id}-${row.field}`} className="border-b border-line/60 px-4 py-4 align-top">
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

function renderCell(car: RecommendedCar, field: string) {
  if (field === "match_score") {
    return <div className="text-lg font-semibold text-steelDeep">{car.match_score}</div>;
  }

  if (field === "risk_flags") {
    return (
      <div className="flex flex-wrap gap-2">
        {car.risk_flags.map((flag) => (
          <span key={`${car.listing_id}-${flag.label}`} className="rounded-md bg-shell px-2 py-1 text-xs text-muted">
            {flag.label}
          </span>
        ))}
      </div>
    );
  }

  const values = car[field as keyof RecommendedCar];
  if (Array.isArray(values)) {
    return (
      <div className="space-y-2">
        {values.map((value) => (
          <div key={`${car.listing_id}-${String(value)}`} className="rounded-md bg-shell px-3 py-2 text-xs text-muted">
            {String(value)}
          </div>
        ))}
      </div>
    );
  }

  return <div className="text-xs text-muted">{String(values)}</div>;
}
