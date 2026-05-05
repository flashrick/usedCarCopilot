"use client";

import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  CarFront,
  CircleDollarSign,
  Flame,
  Loader2,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { formatConsumption, formatMoneyRange } from "@/lib/format";
import { compactLabel, formatTemplate, translateValue } from "@/lib/i18n";
import { marketLabel } from "@/lib/market";
import type { Market, PopularModel, RecommendResponse, RetrieveResponse, Severity, VehicleProfile } from "@/lib/types";

type SearchResultsProps = {
  recommendation: RecommendResponse | null;
  retrieval: RetrieveResponse | null;
  selectedProfileIds: string[];
  onToggleSelection: (id: string) => void;
  onRequestAdvice: () => void;
  recommendationLoading?: boolean;
};

const severityStyles: Record<Severity, string> = {
  low: "border-[#abd600]/40 bg-[#abd600]/10 text-[#d7ff4f]",
  medium: "border-[#ffcc66]/40 bg-[#ffcc66]/10 text-[#ffd68a]",
  high: "border-[#ff8f87]/40 bg-[#ff8f87]/10 text-[#ffb4ab]",
};

export function SearchResults({
  recommendation,
  retrieval,
  selectedProfileIds,
  onToggleSelection,
  onRequestAdvice,
  recommendationLoading,
}: SearchResultsProps) {
  const { copy, locale } = useLocale();
  const selectedSet = new Set(selectedProfileIds);
  const selectedProfiles = retrieval?.vehicle_profiles.filter((profile) => selectedSet.has(profile.profile_id)) ?? [];
  const recommendationProvider =
    typeof recommendation?.debug?.recommendation_provider === "string" ? recommendation.debug.recommendation_provider : null;
  const generationSource = typeof recommendation?.debug?.generation_source === "string" ? recommendation.debug.generation_source : null;
  const overviewStatus = typeof recommendation?.debug?.overview_status === "string" ? recommendation.debug.overview_status : null;
  const showOverviewFallback = Boolean(
    recommendation &&
      !recommendation.recommendation_overview &&
      recommendationProvider &&
      recommendationProvider !== "deterministic" &&
      generationSource === "deterministic_fallback",
  );
  const showOverviewUnavailable = Boolean(
    recommendation &&
      !recommendation.recommendation_overview &&
      recommendationProvider &&
      recommendationProvider !== "deterministic" &&
      generationSource !== "deterministic_fallback" &&
      overviewStatus &&
      overviewStatus !== "generated" &&
      overviewStatus !== "not_requested",
  );

  return (
    <>
      <section className="mx-auto max-w-7xl">
        <SectionTitle
          eyebrow={locale === "zh-CN" ? "热门车型" : "Popular Models"}
          title={locale === "zh-CN" ? "先看当前市场最相关的热门车型" : "Start with the most query-relevant popular models"}
        />
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {retrieval?.popular_models.length ? (
            retrieval.popular_models.map((model) => <PopularModelCard key={model.market_variant_id} model={model} locale={locale} />)
          ) : (
            <EmptyPanel text={locale === "zh-CN" ? "搜索后会先展示热门车型。" : "Popular models will appear after search."} />
          )}
        </div>
      </section>

      <section id="shortlist" className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[0.94fr_1.06fr]">
        <div className="grid content-start gap-4">
          <SectionTitle eyebrow={copy.searchResults.shortlist} title={copy.searchResults.bestMatches} />
          <SelectionToolbar
            count={selectedProfileIds.length}
            countLabel={copy.searchResults.selectedCount}
            helper={copy.searchResults.selectionHint}
            buttonLabel={copy.searchResults.getAdvice}
            buttonLoadingLabel={copy.searchResults.adviceLoading}
            disabled={selectedProfileIds.length < 2 || Boolean(recommendationLoading)}
            loading={recommendationLoading}
            onRequestAdvice={onRequestAdvice}
          />
          {retrieval?.vehicle_profiles.length ? (
            retrieval.vehicle_profiles.map((listing, index) => (
              <ShortlistCard
                key={listing.profile_id}
                listing={listing}
                rank={index + 1}
                selected={selectedSet.has(listing.profile_id)}
                disabled={Boolean(recommendationLoading)}
                onToggle={() => onToggleSelection(listing.profile_id)}
                locale={locale}
                selectLabel={copy.searchResults.selectLabel}
                selectedLabel={copy.searchResults.selectedBadge}
                bodyLabel={copy.queryComposer.body}
                fuelLabel={copy.searchResults.fuel}
                yearLabel={copy.searchResults.year}
                tbcLabel={copy.searchResults.tbc}
              />
            ))
          ) : (
            <EmptyPanel text={copy.searchResults.emptyShortlist} />
          )}
        </div>

        <aside id="advice" className="grid content-start gap-4">
          <SectionTitle eyebrow={copy.searchResults.aiAdvice} title={copy.searchResults.aiAdviceTitle} />
          {recommendationLoading ? (
            <>
              <AdviceLoadingPanel
                title={copy.searchResults.adviceLoadingTitle}
                description={copy.searchResults.adviceLoadingDescription}
                stageOne={copy.searchResults.adviceLoadingStageOne}
                stageTwo={copy.searchResults.adviceLoadingStageTwo}
                stageThree={copy.searchResults.adviceLoadingStageThree}
                selectedProfiles={selectedProfiles.map((profile) => ({
                  id: profile.profile_id,
                  title: profile.title,
                }))}
                selectionCountLabel={formatTemplate(copy.searchResults.adviceLoadingSelectionCount, {
                  count: selectedProfiles.length,
                })}
              />
              <AdviceSkeletonCard />
              <AdviceSkeletonCard />
            </>
          ) : null}
          {recommendation?.recommendation_overview ? (
            <article className="rounded-lg border border-[#00a8ff]/30 bg-[linear-gradient(135deg,rgba(0,168,255,0.18),rgba(0,229,255,0.08))] p-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-[#0d2233] px-2 py-1 text-xs font-semibold text-[#8fd7ff]">
                  {copy.searchResults.overviewEyebrow}
                </span>
                <span className="rounded bg-[#ccff00] px-2 py-1 text-xs font-bold text-[#161e00]">
                  {copy.searchResults.bestMatchBadge}
                </span>
              </div>
              <div className="mt-3 text-sm font-semibold text-white">{copy.searchResults.overviewTitle}</div>
              <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">
                {recommendation.recommendation_overview.recommended_title}
              </h3>
              <p className="mt-2 text-sm leading-7 text-[#d8e9f7]">{recommendation.recommendation_overview.summary}</p>
              <div className="mt-4 inline-flex items-center rounded border border-white/10 bg-black/15 px-3 py-2 text-xs text-[#c6d6e4]">
                {formatTemplate(copy.searchResults.overviewEvidenceCount, {
                  count: recommendation.recommendation_overview.evidence_ids.length,
                })}
              </div>
            </article>
          ) : null}
          {showOverviewFallback ? (
            <div className="rounded-lg border border-[#ffcc66]/40 bg-[#ffcc66]/10 p-4 text-sm text-[#ffd68a]">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{copy.searchResults.overviewFallbackNotice}</span>
              </div>
            </div>
          ) : null}
          {showOverviewUnavailable ? (
            <div className="rounded-lg border border-[#ffcc66]/40 bg-[#ffcc66]/10 p-4 text-sm text-[#ffd68a]">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{copy.searchResults.overviewUnavailableNotice}</span>
              </div>
            </div>
          ) : null}
          {recommendation?.recommended_profiles.length ? (
            recommendation.recommended_profiles.map((car, index) => (
              <article key={car.profile_id} className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded bg-[#007aff] px-2 py-1 text-xs font-bold text-white">#{index + 1}</span>
                      {index === 0 ? (
                        <span className="rounded bg-[#ccff00] px-2 py-1 text-xs font-bold text-[#161e00]">
                          {copy.searchResults.bestMatchBadge}
                        </span>
                      ) : null}
                    </div>
                    <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{car.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{car.valuation_summary}</p>
                  </div>
                  <ScoreGauge score={car.match_score} />
                </div>

                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  <div>
                    <h4 className="font-semibold text-white">{copy.searchResults.matchReasons}</h4>
                    <div className="mt-3 grid gap-2">
                      {car.why_it_matches.map((reason) => (
                        <div key={reason} className="flex items-start gap-2 text-sm leading-6 text-[#c1c6d7]">
                          <BadgeCheck className="mt-1 h-4 w-4 shrink-0 text-[#ccff00]" />
                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-white">{copy.recommendationCard.tradeOffs}</h4>
                    <div className="mt-3 grid gap-2 text-sm leading-6 text-[#c1c6d7]">
                      {car.trade_offs.map((tradeOff) => (
                        <div key={tradeOff} className="flex items-start gap-2">
                          <BadgeCheck className="mt-1 h-4 w-4 shrink-0 text-[#00e5ff]" />
                          <span>{tradeOff}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-4">
                  <h4 className="font-semibold text-white">{copy.searchResults.riskFlags}</h4>
                  <div className="mt-3 grid gap-2">
                    {car.risk_flags.length ? (
                      car.risk_flags.map((flag) => (
                        <div key={`${flag.label}-${flag.reason}`} className={`rounded border p-3 text-sm ${severityStyles[flag.severity]}`}>
                          <div className="font-semibold">{flag.label}</div>
                          <div className="mt-1 leading-6">{flag.reason}</div>
                        </div>
                      ))
                    ) : (
                      <div className="rounded border border-[#abd600]/40 bg-[#abd600]/10 p-3 text-sm text-[#d7ff4f]">
                        {copy.searchResults.noMajorRisk}
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-3">
                  <MetaTile icon={CarFront} label={copy.searchResults.matchScore} value={String(car.match_score)} />
                  <MetaTile icon={ShieldCheck} label={copy.searchResults.matchedCitations} value={String(car.evidence_ids.length)} />
                  <MetaTile icon={ArrowRight} label={copy.searchResults.nextSteps} value={String(car.next_steps.length)} />
                </div>

                <div className="mt-5">
                  <h4 className="font-semibold text-white">{copy.searchResults.nextSteps}</h4>
                  <div className="mt-3 grid gap-2">
                    {car.next_steps.map((step) => (
                      <div key={step} className="flex items-start gap-2 text-sm leading-6 text-[#c1c6d7]">
                        <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-[#00e5ff]" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </article>
            ))
          ) : recommendationLoading ? null : (
            <EmptyPanel text={copy.searchResults.emptyAdvice} />
          )}
        </aside>
      </section>

      <section id="evidence" className="border-t border-white/10 bg-[#111317]">
        <div className="mx-auto max-w-7xl py-8">
          <SectionTitle eyebrow={copy.searchResults.evidenceEyebrow} title={copy.searchResults.evidenceTitle} />
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(recommendation?.evidence ?? []).map((item) => (
              <article key={item.id} className="rounded-lg border border-white/10 bg-[#1e2023] p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="rounded bg-[#00e5ff]/10 px-2 py-1 text-xs font-semibold text-[#bdf4ff]">{compactLabel(item.source_type, locale)}</span>
                  <span className="font-mono text-xs text-[#8b90a0]">{item.id}</span>
                </div>
                <h3 className="mt-3 font-semibold text-white">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{item.snippet}</p>
              </article>
            ))}
            {recommendation?.evidence.length ? null : <EmptyPanel text={copy.searchResults.emptyEvidence} />}
          </div>
        </div>
      </section>
    </>
  );
}

function SelectionToolbar({
  count,
  countLabel,
  helper,
  buttonLabel,
  buttonLoadingLabel,
  disabled,
  loading,
  onRequestAdvice,
}: {
  count: number;
  countLabel: string;
  helper: string;
  buttonLabel: string;
  buttonLoadingLabel: string;
  disabled: boolean;
  loading?: boolean;
  onRequestAdvice: () => void;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-white">{formatTemplate(countLabel, { count })}</div>
          <p className="mt-2 text-sm leading-6 text-[#c1c6d7]">{helper}</p>
        </div>
        <button
          type="button"
          onClick={onRequestAdvice}
          disabled={disabled}
          className="inline-flex h-11 items-center justify-center gap-2 rounded bg-[#00a8ff] px-5 text-sm font-semibold text-white transition hover:bg-[#2ab7ff] disabled:cursor-not-allowed disabled:opacity-70"
        >
          {loading ? <Loader2 className="h-4 w-4 motion-safe:animate-spin" /> : null}
          {loading ? buttonLoadingLabel : buttonLabel}
        </button>
      </div>
    </div>
  );
}

function SectionTitle({ eyebrow, title }: { eyebrow: string; title: string }) {
  return (
    <div>
      <div className="text-sm font-semibold text-[#bdf4ff]">{eyebrow}</div>
      <h2 className="mt-1 font-[var(--font-space-grotesk)] text-2xl font-semibold text-white">{title}</h2>
    </div>
  );
}

function ShortlistCard({
  listing,
  rank,
  selected,
  disabled,
  onToggle,
  locale,
  selectLabel,
  selectedLabel,
  bodyLabel,
  fuelLabel,
  yearLabel,
  tbcLabel,
}: {
  listing: VehicleProfile;
  rank: number;
  selected: boolean;
  disabled?: boolean;
  onToggle: () => void;
  locale: "en" | "zh-CN";
  selectLabel: string;
  selectedLabel: string;
  bodyLabel: string;
  fuelLabel: string;
  yearLabel: string;
  tbcLabel: string;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={disabled}
      className={`w-full rounded-lg border p-4 text-left transition disabled:cursor-wait disabled:opacity-80 ${
        selected ? "border-[#00e5ff] bg-[#1e2023]" : "border-white/10 bg-[#1a1c1f] hover:border-[#00e5ff]/50"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-[#007aff] px-2 py-1 text-xs font-bold text-white">#{rank}</span>
            <span
              className={`rounded px-2 py-1 text-xs font-bold ${
                selected ? "bg-[#ccff00] text-[#161e00]" : "bg-white/8 text-[#d6e3f2]"
              }`}
            >
              {selected ? selectedLabel : selectLabel}
            </span>
          </div>
          <h3 className="mt-3 font-[var(--font-space-grotesk)] text-xl font-semibold text-white">{listing.title}</h3>
          <div className="mt-2 flex flex-wrap gap-3 text-sm text-[#c1c6d7]">
            {listing.estimated_price_min_nzd ? (
              <span className="inline-flex items-center gap-1">
                <CircleDollarSign className="h-4 w-4 text-[#abd600]" />{" "}
                {formatMoneyRange(listing.estimated_price_min_nzd, listing.estimated_price_max_nzd, locale, listing.market)}
              </span>
            ) : null}
            {listing.fuel_consumption_l_per_100km ? <span>{formatConsumption(listing.fuel_consumption_l_per_100km)}</span> : null}
            <span>{listing.engine_description}</span>
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <MetaTile icon={CarFront} label={bodyLabel} value={translateValue(listing.body_type, locale)} />
        <MetaTile icon={Zap} label={fuelLabel} value={translateValue(listing.fuel_type, locale)} />
        <MetaTile icon={ShieldCheck} label={yearLabel} value={`${listing.year_start}-${listing.year_end}`} />
      </div>
    </button>
  );
}

function PopularModelCard({ model, locale }: { model: PopularModel; locale: "en" | "zh-CN" }) {
  return (
    <article className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-[#ff7a00] px-2 py-1 text-xs font-bold text-white">#{model.popularity_rank}</span>
            <span className="rounded bg-white/8 px-2 py-1 text-xs text-[#d6e3f2]">{marketLabel(model.market as Market, locale)}</span>
          </div>
          <h3 className="mt-3 font-[var(--font-space-grotesk)] text-lg font-semibold text-white">{model.display_name}</h3>
          <p className="mt-2 text-sm text-[#9fb4c9]">
            {model.year_start}-{model.year_end}
          </p>
        </div>
        <div className="rounded-lg bg-[#ff7a00]/10 p-2 text-[#ffb066]">
          <Flame className="h-4 w-4" />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        {model.body_types.map((bodyType) => (
          <span key={bodyType} className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[#d6e3f2]">
            {translateValue(bodyType, locale)}
          </span>
        ))}
        {model.fuel_types.map((fuelType) => (
          <span key={fuelType} className="rounded-full border border-[#00e5ff]/20 bg-[#00e5ff]/10 px-2 py-1 text-[#bdf4ff]">
            {translateValue(fuelType, locale)}
          </span>
        ))}
      </div>

      <div className="mt-4 grid gap-2 text-sm leading-6 text-[#c1c6d7]">
        {model.match_reasons.map((reason) => (
          <div key={reason} className="flex items-start gap-2">
            <BadgeCheck className="mt-1 h-4 w-4 shrink-0 text-[#ffb066]" />
            <span>{reason}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function MetaTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof CarFront;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-[#111317] p-3">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#8b90a0]">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <div className="mt-2 text-sm text-white">{value}</div>
    </div>
  );
}

function ScoreGauge({ score }: { score: number }) {
  return (
    <div className="rounded-full border border-[#00e5ff]/30 bg-[#00e5ff]/10 px-4 py-3 text-center">
      <div className="text-[11px] uppercase tracking-[0.18em] text-[#9ddfff]">Score</div>
      <div className="mt-1 text-2xl font-semibold text-white">{score}</div>
    </div>
  );
}

function AdviceLoadingPanel({
  title,
  description,
  stageOne,
  stageTwo,
  stageThree,
  selectedProfiles,
  selectionCountLabel,
}: {
  title: string;
  description: string;
  stageOne: string;
  stageTwo: string;
  stageThree: string;
  selectedProfiles: Array<{ id: string; title: string }>;
  selectionCountLabel: string;
}) {
  return (
    <article className="rounded-2xl border border-[#00a8ff]/25 bg-[linear-gradient(135deg,rgba(0,168,255,0.2),rgba(9,17,27,0.96)_55%,rgba(138,230,106,0.14))] p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#00e5ff]/25 bg-[#00e5ff]/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#bdf4ff]">
            <Loader2 className="h-4 w-4 motion-safe:animate-spin" />
            {title}
          </div>
          <p className="mt-3 text-sm leading-7 text-[#d8e9f7]">{description}</p>
        </div>
        <div className="rounded-full border border-[#8ae66a]/25 bg-[#8ae66a]/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#d8ffcb]">
          {selectionCountLabel}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {selectedProfiles.map((profile) => (
          <span
            key={profile.id}
            className="rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-xs font-medium text-[#e6eef8]"
          >
            {profile.title}
          </span>
        ))}
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {[stageOne, stageTwo, stageThree].map((stage, index) => (
          <div key={stage} className="rounded-xl border border-white/10 bg-black/15 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#00a8ff]/18 text-sm font-semibold text-[#bdf4ff]">
                {index + 1}
              </div>
              <div className="text-sm font-medium text-white">{stage}</div>
            </div>
          </div>
        ))}
      </div>
    </article>
  );
}

function AdviceSkeletonCard() {
  return (
    <article className="rounded-lg border border-white/10 bg-[#1a1c1f] p-4 motion-safe:animate-pulse">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <div className="h-6 w-10 rounded bg-white/10" />
            <div className="h-6 w-24 rounded bg-[#ccff00]/20" />
          </div>
          <div className="mt-3 h-7 w-3/4 rounded bg-white/10" />
          <div className="mt-3 h-4 w-full rounded bg-white/10" />
          <div className="mt-2 h-4 w-5/6 rounded bg-white/10" />
        </div>
        <div className="h-16 w-16 rounded-full border border-[#00e5ff]/20 bg-[#00e5ff]/8" />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="h-20 rounded-lg border border-white/10 bg-[#111317]" />
        <div className="h-20 rounded-lg border border-white/10 bg-[#111317]" />
        <div className="h-20 rounded-lg border border-white/10 bg-[#111317]" />
      </div>

      <div className="mt-5 grid gap-2">
        <div className="h-4 w-full rounded bg-white/10" />
        <div className="h-4 w-11/12 rounded bg-white/10" />
        <div className="h-4 w-4/5 rounded bg-white/10" />
      </div>
    </article>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-white/12 bg-[#151b22] p-5 text-sm leading-6 text-[#c1c6d7]">
      {text}
    </div>
  );
}
