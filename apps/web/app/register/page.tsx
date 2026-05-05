"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import type { Route } from "next";
import { useRouter } from "next/navigation";
import { ArrowRight, UserRoundPlus } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";
import { useLocale } from "@/components/i18n/locale-provider";
import { registerUser } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const { copy } = useLocale();
  const { isLoading, refreshUser, setUser, user } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [nextPath, setNextPath] = useState("/history");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setNextPath(params.get("next") || "/history");
  }, []);

  useEffect(() => {
    if (!isLoading && user) {
      router.replace(nextPath as Route);
    }
  }, [isLoading, nextPath, router, user]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const session = await registerUser({ email, password });
      setUser(session.user);
      await refreshUser();
      router.replace(nextPath as Route);
      router.refresh();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : copy.findQuery.adviceFailed);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
        <section className="surface-card p-5 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="font-[var(--font-space-grotesk)] text-3xl font-semibold text-textStrong">{copy.auth.registerTitle}</h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-textBody">{copy.auth.registerDescription}</p>
            </div>
            <span className="inline-flex rounded-xl bg-primarySoft p-2 text-primary">
              <UserRoundPlus className="h-5 w-5" />
            </span>
          </div>

          {user && !isLoading ? <div className="status-success mt-5">{copy.auth.duplicateSession}</div> : null}

          <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
            <label className="grid gap-2 text-sm text-textBody">
              {copy.auth.email}
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="theme-input"
                autoComplete="email"
              />
            </label>
            <label className="grid gap-2 text-sm text-textBody">
              {copy.auth.password}
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="theme-input"
                autoComplete="new-password"
              />
            </label>

            {error ? <div className="status-danger">{error}</div> : null}

            <div className="flex flex-wrap items-center gap-3">
              <button type="submit" disabled={submitting} className="btn-primary h-11">
                {submitting ? copy.auth.loading : copy.auth.submitRegister}
                <ArrowRight className="h-4 w-4" />
              </button>
              <Link href={`/login?next=${encodeURIComponent(nextPath)}`} className="btn-secondary h-11">
                {copy.auth.switchToLogin}
              </Link>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
