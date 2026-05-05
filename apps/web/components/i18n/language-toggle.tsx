"use client";

import { Languages } from "lucide-react";
import { localeOptions } from "@/lib/i18n";
import { useLocale } from "@/components/i18n/locale-provider";

export function LanguageToggle({ floating = true }: { floating?: boolean }) {
  const { locale, copy, setLocale } = useLocale();

  return (
    <div
      className={`rounded-full border border-line/80 bg-white/92 px-2 py-2 shadow-panel backdrop-blur ${
        floating ? "fixed right-4 top-4 z-50 md:right-6 md:top-6" : ""
      }`}
    >
      <div className="flex items-center gap-2">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primarySoft text-primaryDeep">
          <Languages className="h-4 w-4" />
        </span>
        <span className="text-xs font-semibold text-muted">{copy.languageToggle.label}</span>
        <div className="flex items-center rounded-full bg-shell p-1">
          {localeOptions.map((option) => {
            const active = option.value === locale;
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => setLocale(option.value)}
                className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                  active ? "bg-primary text-white shadow-soft" : "text-mutedSoft hover:text-primaryDeep"
                }`}
                aria-pressed={active}
                title={option.label}
              >
                {option.shortLabel}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
