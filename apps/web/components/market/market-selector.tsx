"use client";

import { MapPinned } from "lucide-react";
import { marketLabel } from "@/lib/market";
import type { Locale } from "@/lib/i18n";
import type { Market } from "@/lib/types";

export function MarketSelector({
  market,
  locale,
  onChange,
}: {
  market: Market;
  locale: Locale;
  onChange: (market: Market) => void;
}) {
  return (
    <label className="grid gap-2 text-sm text-[#c5d3e2]">
      <span className="inline-flex items-center gap-2 text-sm font-medium text-[#dce9f6]">
        <MapPinned className="h-4 w-4 text-[#8fd7ff]" />
        {locale === "zh-CN" ? "地区" : "Region"}
      </span>
      <div className="inline-flex rounded-2xl border border-white/10 bg-[#0d151f] p-1">
        {(["US", "CN"] as const).map((option) => {
          const active = option === market;
          return (
            <button
              key={option}
              type="button"
              onClick={() => onChange(option)}
              className={`rounded-xl px-4 py-2 text-sm transition ${
                active ? "bg-[#00a8ff] text-white" : "text-[#b8c7d6] hover:bg-white/8"
              }`}
            >
              {marketLabel(option, locale)}
            </button>
          );
        })}
      </div>
    </label>
  );
}
