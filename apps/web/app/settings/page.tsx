const providers = [
  {
    name: "Deterministic",
    model: "deterministic_ranker_with_citations",
    note: "Local fallback and default development path.",
  },
  {
    name: "OpenAI",
    model: "gpt-5-mini",
    note: "Responses API with Structured Outputs and local citation validation.",
  },
  {
    name: "DeepSeek",
    model: "deepseek-chat",
    note: "OpenAI-compatible Chat Completions path with JSON-mode parsing.",
  },
  {
    name: "Qwen",
    model: "qwen-plus",
    note: "DashScope compatible-mode Chat Completions path.",
  },
  {
    name: "Kimi",
    model: "kimi-k2.6",
    note: "Moonshot OpenAI-compatible Chat Completions path.",
  },
];

export default function SettingsPage() {
  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">Provider Matrix</div>
          <h2 className="mt-1 text-2xl font-semibold">Recommendation provider options</h2>
          <div className="mt-4 space-y-3">
            {providers.map((provider) => (
              <article key={provider.name} className="rounded-md bg-shell p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{provider.name}</div>
                    <div className="mt-1 font-mono text-xs text-muted">{provider.model}</div>
                  </div>
                  <div className="rounded-md bg-white px-3 py-2 text-xs text-muted">Selectable</div>
                </div>
                <p className="mt-3 text-sm text-muted">{provider.note}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted">Runtime Notes</div>
          <div className="mt-4 space-y-3 text-sm text-muted">
            <div className="rounded-md bg-shell p-4">
              External provider failures fall back to deterministic recommendations. The backend surfaces fallback reason
              in `/recommend.debug`.
            </div>
            <div className="rounded-md bg-shell p-4">
              Embedding generation remains on `local_hash` by default, so retrieval stays reproducible even when the
              recommendation provider changes.
            </div>
            <div className="rounded-md bg-shell p-4 font-mono text-xs">
              NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
