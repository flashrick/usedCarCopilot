#!/usr/bin/env python3
"""Build and diff market-aware safety-rating seed artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from scripts.sync_seed_common import (
        DEFAULT_SEED_DIR,
        build_sync_parser,
        diff_by_id,
        read_json,
        write_json,
        write_jsonl,
    )
except ModuleNotFoundError:
    from sync_seed_common import (
        DEFAULT_SEED_DIR,
        build_sync_parser,
        diff_by_id,
        read_json,
        write_json,
        write_jsonl,
    )


DEFAULT_SOURCE_PATH = DEFAULT_SEED_DIR / "market_catalog_seed.json"


@dataclass(frozen=True)
class BuildResult:
    safety_ratings: list[dict[str, Any]]


def build_outputs(source: dict[str, Any], market: str) -> BuildResult:
    safety_ratings: list[dict[str, Any]] = []
    for item in list(source.get("models", [])):
        item_market = str(item.get("market", "")).upper()
        if market != "ALL" and item_market != market:
            continue
        for profile in item.get("profiles", []):
            safety_ratings.append(
                {
                    "profile_id": profile["profile_id"],
                    "market_variant_id": item["market_variant_id"],
                    "market": item_market,
                    "brand": item["brand"],
                    "model": item["model"],
                    "year_start": profile["year_start"],
                    "year_end": profile["year_end"],
                    "safety_rating_stars": profile.get("safety_rating_stars"),
                    "safety_rating_source": profile.get("safety_rating_source"),
                    "safety_rating_status": profile.get("safety_rating_status"),
                }
            )
    safety_ratings.sort(key=lambda row: (row["market"], row["brand"], row["model"], row["year_start"], row["profile_id"]))
    return BuildResult(safety_ratings=safety_ratings)


def write_outputs(seed_dir: Path, result: BuildResult) -> None:
    write_jsonl(seed_dir / "safety_ratings.jsonl", result.safety_ratings)


def snapshot_payload(result: BuildResult) -> dict[str, Any]:
    return {"safety_ratings": result.safety_ratings}


def build_diff(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    return {
        "safety_ratings_added": diff_by_id(previous.get("safety_ratings", []), current.get("safety_ratings", []), "profile_id"),
        "counts": {
            "previous_safety_ratings": len(previous.get("safety_ratings", [])),
            "current_safety_ratings": len(current.get("safety_ratings", [])),
        },
    }


def run_build(seed_dir: Path, source_path: Path, market: str, snapshot_dir: Path) -> None:
    source = read_json(source_path)
    result = build_outputs(source, market)
    write_outputs(seed_dir, result)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_name = f"safety-ratings-{market.lower()}-latest.json"
    write_json(snapshot_dir / snapshot_name, snapshot_payload(result))
    print(f"Built safety ratings seed for market={market}")
    print(f"- safety_ratings: {len(result.safety_ratings)}")


def run_diff(seed_dir: Path, source_path: Path, market: str, snapshot_dir: Path, report_path: Path | None) -> None:
    source = read_json(source_path)
    result = build_outputs(source, market)
    current = snapshot_payload(result)
    snapshot_name = f"safety-ratings-{market.lower()}-latest.json"
    previous_path = snapshot_dir / snapshot_name
    previous = read_json(previous_path) if previous_path.exists() else {}
    diff = build_diff(previous, current)
    output_path = report_path or (snapshot_dir / f"safety-ratings-{market.lower()}-diff.json")
    write_json(output_path, diff)
    print(f"Wrote diff report to {output_path}")
    print(diff["counts"])


def main() -> None:
    parser = build_sync_parser(
        description="Build or diff market-aware safety-rating seed artifacts.",
        default_source=DEFAULT_SOURCE_PATH,
    )
    args = parser.parse_args()

    market = args.market.upper()
    if args.mode == "build":
        run_build(args.seed_dir, args.source, market, args.snapshot_dir)
        return
    run_diff(args.seed_dir, args.source, market, args.snapshot_dir, args.report)


if __name__ == "__main__":
    main()
