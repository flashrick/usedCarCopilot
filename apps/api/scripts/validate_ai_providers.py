#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.provider_validation import (
    ProviderValidationConfig,
    SUPPORTED_LIVE_PROVIDERS,
    format_provider_validation_summary,
    run_provider_validation,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate live AI recommendation providers against the existing recommendation contract."
    )
    parser.add_argument(
        "--provider",
        action="append",
        choices=SUPPORTED_LIVE_PROVIDERS,
        help="Provider to validate. May be supplied multiple times. Defaults to all live providers.",
    )
    parser.add_argument(
        "--query",
        default="I need a reliable car under $12,000 for commuting in Auckland.",
        help="Validation query sent through retrieval and recommendation generation.",
    )
    parser.add_argument("--limit", type=int, default=3, help="Recommendation limit.")
    parser.add_argument(
        "--include-missing",
        action="store_true",
        help="Call providers even when their API key is missing, which should exercise deterministic fallback.",
    )
    parser.add_argument("--json-output", type=Path, default=None, help="Optional path for full JSON results.")
    parser.add_argument(
        "--fail-on-skip",
        action="store_true",
        help="Exit with failure when any selected provider is skipped because its API key is missing.",
    )
    args = parser.parse_args()

    providers = tuple(args.provider or SUPPORTED_LIVE_PROVIDERS)
    summary = run_provider_validation(
        ProviderValidationConfig(
            providers=providers,
            query=args.query,
            limit=args.limit,
            include_missing=args.include_missing,
        )
    )

    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(format_provider_validation_summary(summary))

    if summary["failed"] or (args.fail_on_skip and summary["skipped"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
