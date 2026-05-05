"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { Activity, AlertTriangle, Database, RefreshCcw } from "lucide-react";
import { useLocale } from "@/components/i18n/locale-provider";
import { fetchAdminReports } from "@/lib/api";
import type { AdminReportsResponse, ReportBucket, ReportMetric, ReportRecentItem } from "@/lib/types";

type ReportState = {
  data: AdminReportsResponse | null;
  error: string | null;
};

export default function AdminReportsPage() {
  const { copy } = useLocale();
  const [state, setState] = useState<ReportState>({ data: null, error: null });
  const [isRefreshing, startRefresh] = useTransition();

  function loadReports() {
    startRefresh(async () => {
      try {
        const data = await fetchAdminReports();
        setState({ data, error: null });
      } catch (error) {
        setState((current) => ({
          data: current.data,
          error: error instanceof Error ? error.message : copy.adminReports.loadFailed,
        }));
      }
    });
  }

  useEffect(() => {
    loadReports();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const generatedAt = useMemo(() => formatTimestamp(state.data?.generated_at), [state.data?.generated_at]);

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl">
              <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{copy.adminReports.eyebrow}</div>
              <h2 className="mt-2 text-2xl font-semibold">{copy.adminReports.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted">{copy.adminReports.description}</p>
              <p className="mt-3 text-xs text-mutedSoft">
                {copy.adminReports.generatedAt}: {generatedAt}
              </p>
            </div>
            <button type="button" onClick={loadReports} disabled={isRefreshing} className="btn-secondary h-11 rounded-md px-4">
              <RefreshCcw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              {isRefreshing ? copy.adminReports.refreshing : copy.adminReports.refresh}
            </button>
          </div>
        </section>

        {state.error ? (
          <div className="status-danger">
            <AlertTriangle className="h-4 w-4" />
            {state.error}
          </div>
        ) : null}

        {state.data ? (
          <>
            <MetricGrid title={copy.adminReports.summary} metrics={state.data.summary} icon="database" />

            <div className="grid gap-4 xl:grid-cols-3">
              <MetricPanel title={copy.adminReports.retrieval} metrics={state.data.retrieval_activity} />
              <MetricPanel title={copy.adminReports.ai} metrics={state.data.ai_activity} />
              <MetricPanel title={copy.adminReports.ingestion} metrics={state.data.ingestion_activity} />
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <BucketPanel title={copy.adminReports.profilesByMarket} buckets={state.data.profiles_by_market} />
              <BucketPanel title={copy.adminReports.profilesByBody} buckets={state.data.profiles_by_body_type} />
              <BucketPanel title={copy.adminReports.profilesByFuel} buckets={state.data.profiles_by_fuel_type} />
              <BucketPanel title={copy.adminReports.profilesByPrice} buckets={state.data.profiles_by_price_band} />
              <BucketPanel title={copy.adminReports.knowledgeBySource} buckets={state.data.knowledge_by_source_type} />
              <BucketPanel title={copy.adminReports.knowledgeByEvidence} buckets={state.data.knowledge_by_evidence_level} />
              <BucketPanel title={copy.adminReports.retrievalByEndpoint} buckets={state.data.retrieval_by_endpoint} />
              <BucketPanel title={copy.adminReports.aiByProvider} buckets={state.data.ai_by_provider} />
            </div>

            <div className="grid gap-4 xl:grid-cols-3">
              <RecentPanel title={copy.adminReports.recentRetrieval} items={state.data.recent_retrieval_requests} />
              <RecentPanel title={copy.adminReports.recentAi} items={state.data.recent_ai_requests} />
              <RecentPanel title={copy.adminReports.recentIngestion} items={state.data.recent_ingestion_runs} />
            </div>
          </>
        ) : (
          <section className="rounded-md border border-dashed border-line/70 bg-panel p-5 text-sm text-muted">
            {isRefreshing ? copy.adminReports.refreshing : copy.adminReports.empty}
          </section>
        )}
      </div>
    </div>
  );
}

function MetricGrid({ title, metrics, icon }: { title: string; metrics: ReportMetric[]; icon: "database" | "activity" }) {
  const Icon = icon === "database" ? Database : Activity;
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Icon className="h-4 w-4 text-primary" />
        {title}
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricTile key={metric.label} metric={metric} />
        ))}
      </div>
    </section>
  );
}

function MetricPanel({ title, metrics }: { title: string; metrics: ReportMetric[] }) {
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-4 grid gap-3">
        {metrics.map((metric) => (
          <MetricTile key={metric.label} metric={metric} compact />
        ))}
      </div>
    </section>
  );
}

function MetricTile({ metric, compact = false }: { metric: ReportMetric; compact?: boolean }) {
  return (
    <div className={`rounded-md bg-shell px-4 ${compact ? "py-3" : "py-4"}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="text-xs uppercase tracking-[0.18em] text-muted">{metric.label}</div>
        {metric.status ? <span className={`h-2.5 w-2.5 rounded-full ${statusDotClass(metric.status)}`} /> : null}
      </div>
      <div className="mt-2 text-2xl font-semibold">{metric.value}</div>
      {metric.helper ? <p className="mt-2 text-xs leading-5 text-mutedSoft">{metric.helper}</p> : null}
    </div>
  );
}

function BucketPanel({ title, buckets }: { title: string; buckets: ReportBucket[] }) {
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-4 grid gap-3">
        {buckets.length ? (
          buckets.map((bucket) => <BucketRow key={bucket.label} bucket={bucket} />)
        ) : (
          <div className="rounded-md border border-dashed border-line/70 px-4 py-3 text-sm text-muted">No data</div>
        )}
      </div>
    </section>
  );
}

function BucketRow({ bucket }: { bucket: ReportBucket }) {
  const width = Math.max(4, Math.min(100, bucket.percentage ?? 0));
  return (
    <div className="grid gap-2">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-medium">{bucket.label}</span>
        <span className="text-muted">
          {bucket.count} {bucket.percentage !== null && bucket.percentage !== undefined ? `(${bucket.percentage.toFixed(1)}%)` : ""}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-shellDeep">
        <div className="h-full rounded-full bg-secondary" style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function RecentPanel({ title, items }: { title: string; items: ReportRecentItem[] }) {
  return (
    <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-4 grid gap-3">
        {items.length ? (
          items.map((item, index) => (
            <div key={`${item.title}-${item.timestamp ?? index}`} className="rounded-md bg-shell px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0 font-medium">{item.title}</div>
                {item.status ? (
                  <span className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-semibold ${statusPillClass(item.status)}`}>
                    {item.status}
                  </span>
                ) : null}
              </div>
              {item.subtitle ? <p className="mt-2 line-clamp-2 text-xs leading-5 text-muted">{item.subtitle}</p> : null}
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-mutedSoft">
                <span>{item.value}</span>
                <span>{formatTimestamp(item.timestamp)}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-md border border-dashed border-line/70 px-4 py-3 text-sm text-muted">No recent activity</div>
        )}
      </div>
    </section>
  );
}

function statusDotClass(status: string) {
  if (status === "ok" || status === "completed" || status === "success") {
    return "bg-success";
  }
  if (status === "warning" || status === "running") {
    return "bg-accent";
  }
  return "bg-riskHighInk";
}

function statusPillClass(status: string) {
  if (status === "ok" || status === "completed" || status === "success") {
    return "bg-riskLow text-riskLowInk";
  }
  if (status === "warning" || status === "running") {
    return "bg-riskMedium text-riskMediumInk";
  }
  return "bg-riskHigh text-riskHighInk";
}

function formatTimestamp(value?: string | null) {
  if (!value) {
    return "N/A";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "N/A";
  }
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
