import fs from "node:fs/promises";
import path from "node:path";
import type { EvalSummary } from "@/lib/types";

export default async function EvalPage() {
  const [retrievalSummary, recommendationSummary] = await Promise.all([
    parseEvalFile(path.resolve(process.cwd(), "../../documents/eval-report.md"), "Retrieval Eval"),
    parseEvalFile(path.resolve(process.cwd(), "../../documents/recommendation-eval-report.md"), "Recommendation Eval"),
  ]);

  return (
    <div className="p-4 md:p-6 xl:p-8">
      <div className="grid gap-4 xl:grid-cols-2">
        {[retrievalSummary, recommendationSummary].map((summary) => (
          <section key={summary.title} className="rounded-md border border-line/70 bg-panel p-4 shadow-panel">
            <div className="text-[11px] uppercase tracking-[0.22em] text-muted">{summary.title}</div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {summary.metrics.map((metric) => (
                <div key={metric.label} className="rounded-md bg-shell px-4 py-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-muted">{metric.label}</div>
                  <div className="mt-1 text-xl font-semibold">{metric.value}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-md bg-shell p-4">
              <div className="text-sm font-medium">Weakest cases</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {summary.weakestCases.map((value) => (
                  <span key={value} className="rounded-md bg-white px-3 py-2 text-xs text-muted">
                    {value}
                  </span>
                ))}
              </div>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

async function parseEvalFile(filePath: string, title: string): Promise<EvalSummary> {
  const content = await fs.readFile(filePath, "utf-8");
  const metrics = Array.from(content.matchAll(/^- ([^:]+): (.+)$/gm))
    .slice(0, 6)
    .map((match) => ({ label: match[1], value: match[2] }));
  const weakestCases = Array.from(content.matchAll(/^### (eval-\d+)/gm)).slice(0, 5).map((match) => match[1]);
  return { title, metrics, weakestCases };
}
