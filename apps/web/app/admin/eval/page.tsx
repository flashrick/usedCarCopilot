import fs from "node:fs/promises";
import path from "node:path";
import { EvalSummaryGrid } from "@/components/eval/eval-summary-grid";
import type { EvalSummary } from "@/lib/types";
import { getCopy, defaultLocale } from "@/lib/i18n";

export default async function EvalPage() {
  const copy = getCopy(defaultLocale);
  const [retrievalSummary, recommendationSummary] = await Promise.all([
    parseEvalFile(path.resolve(process.cwd(), "../../documents/eval-report.md"), copy.eval.retrievalTitle),
    parseEvalFile(path.resolve(process.cwd(), "../../documents/recommendation-eval-report.md"), copy.eval.recommendationTitle),
  ]);

  return <EvalSummaryGrid summaries={[retrievalSummary, recommendationSummary]} />;
}

async function parseEvalFile(filePath: string, title: string): Promise<EvalSummary> {
  const content = await fs.readFile(filePath, "utf-8");
  const metrics = Array.from(content.matchAll(/^- ([^:]+): (.+)$/gm))
    .slice(0, 6)
    .map((match) => ({ label: match[1], value: match[2] }));
  const weakestCases = Array.from(content.matchAll(/^### (eval-\d+)/gm)).slice(0, 5).map((match) => match[1]);
  return { title, metrics, weakestCases };
}
