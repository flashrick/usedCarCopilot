"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { CarFront, History, LogIn, LogOut, Search } from "lucide-react";
import { LanguageToggle } from "@/components/i18n/language-toggle";
import { useLocale } from "@/components/i18n/locale-provider";
import { useAuth } from "@/components/auth/auth-provider";
import { logoutUser } from "@/lib/api";

export function SiteChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (pathname.startsWith("/admin")) {
    return (
      <>
        <LanguageToggle />
        {children}
      </>
    );
  }

  return (
    <>
      <PublicHeader />
      {children}
    </>
  );
}

function PublicHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const { copy } = useLocale();
  const { user, isLoading, setUser } = useAuth();

  async function handleLogout() {
    try {
      await logoutUser();
    } finally {
      setUser(null);
      router.push("/");
      router.refresh();
    }
  }

  const navItemClass = (href: string) =>
    `inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm transition ${
      pathname === href || pathname.startsWith(`${href}/`)
        ? "bg-primarySoft text-primaryDeep"
        : "text-textBody hover:bg-white hover:text-textStrong"
    }`;

  return (
    <header className="border-b border-line/70 bg-white/82 backdrop-blur">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/" className="inline-flex items-center gap-3 text-textStrong">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-white shadow-soft">
              <CarFront className="h-5 w-5" />
            </span>
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-secondaryDeep/80">{copy.siteNav.brandEyebrow}</div>
              <div className="text-lg font-semibold">{copy.siteNav.brandTitle}</div>
            </div>
          </Link>
          <nav className="flex flex-wrap items-center gap-1 rounded-full bg-shell/80 p-1">
            <Link href="/find/query" className={navItemClass("/find/query")}>
              <Search className="h-4 w-4" />
              {copy.siteNav.search}
            </Link>
            <Link href="/history" className={navItemClass("/history")}>
              <History className="h-4 w-4" />
              {copy.siteNav.history}
            </Link>
          </nav>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <LanguageToggle floating={false} />
          {user ? (
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-shell px-3 py-2 text-sm text-textBody">{user.email}</span>
              <button type="button" onClick={() => void handleLogout()} className="btn-secondary h-11 rounded-full px-4">
                <LogOut className="h-4 w-4" />
                {copy.siteNav.logout}
              </button>
            </div>
          ) : isLoading ? (
            <div className="rounded-full bg-shell px-3 py-2 text-sm text-muted">{copy.siteNav.loading}</div>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <Link href="/login" className="btn-secondary h-11 rounded-full px-4">
                <LogIn className="h-4 w-4" />
                {copy.siteNav.login}
              </Link>
              <Link href="/register" className="btn-primary h-11 rounded-full px-4">
                {copy.siteNav.register}
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
