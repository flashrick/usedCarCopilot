"use client";

import { FileStack, History, Sparkles } from "lucide-react";
import { RecommendationCard } from "@/components/workbench/recommendation-card";
import { useLocale } from "@/components/i18n/locale-provider";
import { compactLabel, formatTemplate } from "@/lib/i18n";
import type { RecommendResponse } from "@/lib/types";

export function RecommendationHistoryView({ recommendation }: { recommendation: RecommendResponse }) {
  const { copy, locale } = useLocale();
  const overview = recommendation.recommendation_overview;

  return (
    <div className="grid gap-6">
      {overview ? (
        <section className="surface-card p-5 md:p-6">
          <div className="flex items-start gap-3">
            <span className="inline-flex rounded-xl bg-primarySoft p-2 text-primary">
              <Sparkles className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <div className="section-eyebrow">{copy.searchResults.overviewEyebrow}</div>
              <h2 className="mt-2 text-2xl font-semibold text-textStrong">{overview.recommended_title}</h2>
              <p className="mt-3 max-w-4xl text-sm leading-7 text-textBody">{overview.summary}</p>
              <p className="mt-3 text-xs text-muted">
                {formatTemplate(copy.searchResults.overviewEvidenceCount, { count: overview.evidence_ids.length })}
              </p>
            </div>
          </div>
        </section>
      ) : null}

      <section className="grid gap-4">
        <div className="flex items-center gap-3">
          <span className="inline-flex rounded-xl bg-secondarySoft p-2 text-secondaryDeep">
            <History className="h-5 w-5" />
          </span>
          <div>
            <div className="section-eyebrow">{copy.searchResults.finalDecisionEyebrow}</div>
            <h2 className="text-2xl font-semibold text-textStrong">{copy.history.detailTitle}</h2>
          </div>
        </div>
        <div className={`grid gap-4 ${recommendation.recommended_profiles.length > 1 ? "lg:grid-cols-2" : ""}`}>
          {recommendation.recommended_profiles.map((profile) => (
            <RecommendationCard key={profile.profile_id} car={profile} />
          ))}
        </div>
      </section>

      <section className="border-t border-line/70 bg-white/55">
        <div className="py-6">
          <div className="flex items-center gap-3">
            <span className="inline-flex rounded-xl bg-secondarySoft p-2 text-secondaryDeep">
              <FileStack className="h-5 w-5" />
            </span>
            <div>
              <div className="section-eyebrow">{copy.searchResults.evidenceEyebrow}</div>
              <h2 className="text-2xl font-semibold text-textStrong">{copy.searchResults.evidenceTitle}</h2>
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {recommendation.evidence.map((item) => (
              <article key={item.id} className="surface-card min-w-0 p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="rounded-full bg-secondarySoft px-2.5 py-1 text-xs font-semibold text-secondaryDeep">
                    {compactLabel(item.source_type, locale)}
                  </span>
                  <span className="font-mono text-xs text-mutedSoft">{item.id}</span>
                </div>
                <h3 className="mt-3 break-words font-semibold text-textStrong">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-textBody">{item.snippet}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
