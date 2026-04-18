#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.evaluation.retrieval_eval import (
    RetrievalEvalConfig,
    format_markdown_report,
    format_summary,
    run_retrieval_eval,
)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Run retrieval eval cases against POST /retrieve.")
    parser.add_argument("--api-url", default=f"http://127.0.0.1:{settings.api_port}", help="Base URL for the API.")
    parser.add_argument("--seed-dir", type=Path, default=settings.seed_data_dir, help="Directory containing eval_cases.json.")
    parser.add_argument("--limit", type=int, default=5, help="Retrieve limit sent to /retrieve.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout in seconds.")
    parser.add_argument("--json-output", type=Path, default=None, help="Optional path for full JSON results.")
    parser.add_argument("--markdown-output", type=Path, default=None, help="Optional path for a markdown report.")
    parser.add_argument(
        "--fail-under-model-recall",
        type=float,
        default=None,
        help="Exit with failure when average model recall is below this threshold.",
    )
    parser.add_argument(
        "--fail-under-risk-recall",
        type=float,
        default=None,
        help="Exit with failure when average risk theme recall is below this threshold.",
    )
    args = parser.parse_args()

    config = RetrievalEvalConfig(
        api_url=args.api_url,
        seed_dir=args.seed_dir,
        limit=max(1, min(args.limit, 20)),
        timeout_seconds=args.timeout,
    )
    summary = run_retrieval_eval(config)

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(format_markdown_report(summary), encoding="utf-8")

    print(format_summary(summary))

    failures: list[str] = []
    if args.fail_under_model_recall is not None and summary["average_model_recall"] < args.fail_under_model_recall:
        failures.append(
            f"average model recall {summary['average_model_recall']:.2%} "
            f"is below {args.fail_under_model_recall:.2%}"
        )
    if args.fail_under_risk_recall is not None and summary["average_risk_theme_recall"] < args.fail_under_risk_recall:
        failures.append(
            f"average risk theme recall {summary['average_risk_theme_recall']:.2%} "
            f"is below {args.fail_under_risk_recall:.2%}"
        )

    if failures:
        print("Retrieval eval failed thresholds")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
