"use client";

import type { Listing } from "@/lib/types";
import { formatMileage, formatMoney } from "@/lib/format";

export function RetrievalTable({ listings }: { listings: Listing[] }) {
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">Retrieval Explorer</div>
          <h3 className="mt-1 text-lg font-semibold">Candidate listings in scope</h3>
        </div>
        <div className="rounded-md bg-shell px-3 py-2 text-xs text-muted">{listings.length} visible rows</div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.18em] text-muted">
            <tr>
              {["Vehicle", "Price", "Mileage", "Fuel", "Body", "Location"].map((heading) => (
                <th key={heading} className="border-b border-line/70 px-3 py-3 font-medium">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {listings.map((listing) => (
              <tr key={listing.listing_id} className="border-b border-line/50 last:border-none">
                <td className="px-3 py-3">
                  <div className="font-medium">{listing.title}</div>
                  <div className="mt-1 text-xs text-muted">
                    {listing.brand} {listing.model} {listing.year ? `· ${listing.year}` : ""}
                  </div>
                </td>
                <td className="px-3 py-3">{formatMoney(listing.price)}</td>
                <td className="px-3 py-3">{formatMileage(listing.mileage)}</td>
                <td className="px-3 py-3">{listing.fuel_type ?? "N/A"}</td>
                <td className="px-3 py-3">{listing.body_type ?? "N/A"}</td>
                <td className="px-3 py-3">{listing.location ?? "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
