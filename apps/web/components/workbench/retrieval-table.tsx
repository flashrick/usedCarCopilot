"use client";

import { useLocale } from "@/components/i18n/locale-provider";
import type { Listing } from "@/lib/types";
import { formatMileage, formatMoney } from "@/lib/format";
import { formatTemplate, translateValue } from "@/lib/i18n";

type RetrievalTableProps = {
  listings: Listing[];
  selectedListingIds?: string[];
  onToggleSelection?: (listingId: string) => void;
};

export function RetrievalTable({ listings, selectedListingIds = [], onToggleSelection }: RetrievalTableProps) {
  const { copy, locale } = useLocale();
  const selectionEnabled = Boolean(onToggleSelection);
  const selectedSet = new Set(selectedListingIds);
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.retrievalTable.eyebrow}</div>
          <h3 className="mt-1 text-lg font-semibold">{copy.retrievalTable.title}</h3>
        </div>
        <div className="rounded-md bg-shell px-3 py-2 text-xs text-muted">
          {formatTemplate(copy.retrievalTable.visibleRows, { count: listings.length })}
        </div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase tracking-[0.18em] text-muted">
            <tr>
              {selectionEnabled ? <th className="border-b border-line/70 px-3 py-3 font-medium">{copy.retrievalTable.select}</th> : null}
              {copy.retrievalTable.columns.map((heading) => (
                <th key={heading} className="border-b border-line/70 px-3 py-3 font-medium">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {listings.map((listing) => (
              <tr key={listing.listing_id} className="border-b border-line/50 last:border-none">
                {selectionEnabled ? (
                  <td className="px-3 py-3">
                    <input
                      type="checkbox"
                      checked={selectedSet.has(listing.listing_id)}
                      onChange={() => onToggleSelection?.(listing.listing_id)}
                      className="h-4 w-4 rounded border-line text-steel focus:ring-steel/30"
                    />
                  </td>
                ) : null}
                <td className="px-3 py-3">
                  <div className="font-medium">{listing.title}</div>
                  <div className="mt-1 text-xs text-muted">
                    {listing.brand} {listing.model} {listing.year ? `· ${listing.year}` : ""}
                  </div>
                </td>
                <td className="px-3 py-3">{formatMoney(listing.price, locale)}</td>
                <td className="px-3 py-3">{formatMileage(listing.mileage, locale)}</td>
                <td className="px-3 py-3">{translateValue(listing.fuel_type, locale)}</td>
                <td className="px-3 py-3">{translateValue(listing.body_type, locale)}</td>
                <td className="px-3 py-3">{listing.location ?? copy.common.notAvailable}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
