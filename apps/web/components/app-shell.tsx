"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { BarChart3, CarFront, Files, Gauge, LayoutDashboard, Settings2 } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";

const navigation: Array<{ href: Route; labelKey: keyof ReturnType<typeof useLocale>["copy"]["appShell"]["nav"]; icon: typeof LayoutDashboard }> = [
  { href: "/admin", labelKey: "workbench", icon: LayoutDashboard },
  { href: "/admin/retrieve", labelKey: "retrieval", icon: Files },
  { href: "/admin/compare", labelKey: "compare", icon: CarFront },
  { href: "/admin/reports", labelKey: "reports", icon: BarChart3 },
  { href: "/admin/eval", labelKey: "eval", icon: BarChart3 },
  { href: "/admin/settings", labelKey: "providers", icon: Settings2 },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { copy } = useLocale();

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <div className="mx-auto flex min-h-screen w-full max-w-[1720px] flex-col lg:flex-row">
        <aside className="border-b border-line/70 bg-white/75 px-4 py-4 backdrop-blur lg:w-64 lg:border-b-0 lg:border-r lg:px-5 lg:py-6">
          <div className="flex items-center gap-3 pb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary text-white shadow-soft">
              <Gauge className="h-5 w-5" />
            </div>
            <div>
              <p className="section-eyebrow">{copy.appShell.brandEyebrow}</p>
              <h1 className="text-lg font-semibold">{copy.appShell.brandTitle}</h1>
            </div>
          </div>

          <nav className="grid grid-cols-2 gap-2 md:grid-cols-6 lg:grid-cols-1">
            {navigation.map(({ href, labelKey, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 rounded-md border px-3 py-3 text-sm transition ${
                    active
                      ? "border-primary/20 bg-primarySoft/80 text-primaryDeep shadow-inset"
                      : "border-transparent bg-transparent text-muted hover:border-line/70 hover:bg-white hover:text-ink"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{copy.appShell.nav[labelKey]}</span>
                </Link>
              );
            })}
          </nav>

          <div className="mt-5 rounded-xl border border-line/70 bg-panel/90 p-3 text-xs text-muted shadow-inset lg:mt-8">
            {copy.appShell.note}
          </div>
        </aside>

        <main className="flex-1 bg-transparent">{children}</main>
      </div>
    </div>
  );
}
