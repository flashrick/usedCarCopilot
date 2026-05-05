#!/usr/bin/env python3
"""Build and diff market-aware vehicle catalog seed artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_DIR = ROOT / "data" / "seed"
DEFAULT_SOURCE_PATH = DEFAULT_SEED_DIR / "market_catalog_seed.json"
DEFAULT_SNAPSHOT_DIR = DEFAULT_SEED_DIR / "snapshots"


@dataclass(frozen=True)
class BuildResult:
    canonical_models: list[dict[str, Any]]
    market_variants: list[dict[str, Any]]
    popularity_rankings: list[dict[str, Any]]
    vehicle_profiles: list[dict[str, Any]]
    knowledge_sources: list[dict[str, Any]]
    eval_cases: list[dict[str, Any]]


class Adapter:
    """Placeholder adapter interface for future external catalog sources."""

    name = "placeholder"

    def load(self, market: str) -> list[dict[str, Any]]:
        return []


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def normalize_market(value: str) -> str:
    market = value.strip().upper()
    if market not in {"US", "CN"}:
        raise SystemExit(f"Unsupported market: {value}")
    return market


def select_models(models: list[dict[str, Any]], market: str) -> list[dict[str, Any]]:
    if market == "ALL":
        return models
    return [item for item in models if item.get("market") == market]


def build_outputs(source: dict[str, Any], market: str, snapshot_date: date | None = None) -> BuildResult:
    snapshot = snapshot_date or date.today()
    models = select_models(list(source.get("models", [])), market)
    eval_cases = [
        case
        for case in list(source.get("eval_cases", []))
        if market == "ALL" or normalize_market(str(case.get("market", "US"))) == market
    ]

    canonical_models: dict[str, dict[str, Any]] = {}
    market_variants: list[dict[str, Any]] = []
    popularity_rankings: list[dict[str, Any]] = []
    vehicle_profiles: list[dict[str, Any]] = []
    knowledge_sources: list[dict[str, Any]] = []

    for item in models:
        canonical_model_id = str(item["canonical_model_id"])
        canonical_models.setdefault(
            canonical_model_id,
            {
                "canonical_model_id": canonical_model_id,
                "brand": item["brand"],
                "model": item["model"],
                "canonical_model_slug": item["canonical_model_slug"],
                "aliases": item.get("aliases", []),
            },
        )

        market_variant_id = str(item["market_variant_id"])
        market_variants.append(
            {
                "market_variant_id": market_variant_id,
                "canonical_model_id": canonical_model_id,
                "market": item["market"],
                "brand": item["brand"],
                "model": item["model"],
                "display_name": item["display_name"],
                "local_aliases": item.get("local_aliases", []),
                "year_start": item["year_start"],
                "year_end": item["year_end"],
                "body_types": item.get("body_types", []),
                "fuel_types": item.get("fuel_types", []),
            }
        )

        popularity_rankings.append(
            {
                "market": item["market"],
                "market_variant_id": market_variant_id,
                "popularity_rank": item["popularity_rank"],
                "brand_popularity_rank": item["brand_popularity_rank"],
                "source_label": item.get("source_label", "curated_seed"),
                "snapshot_date": snapshot.isoformat(),
                "match_tags": item.get("match_tags", []),
            }
        )

        for profile in item.get("profiles", []):
            vehicle_profiles.append(
                {
                    **profile,
                    "transmission_detail": profile.get("transmission_detail"),
                    "transmission_maintenance_risk": profile.get("transmission_maintenance_risk"),
                    "transmission_risk_note": profile.get("transmission_risk_note"),
                    "safety_rating_stars": profile.get("safety_rating_stars"),
                    "safety_rating_source": profile.get("safety_rating_source"),
                    "safety_rating_status": profile.get("safety_rating_status"),
                    "market": item["market"],
                    "market_variant_id": market_variant_id,
                    "brand": item["brand"],
                    "model": item["model"],
                }
            )

        for knowledge in item.get("knowledge", []):
            knowledge_sources.append(
                {
                    **knowledge,
                    "market": item["market"],
                    "market_variant_id": market_variant_id,
                    "brand": item["brand"],
                    "model": item["model"],
                    "profile_id": knowledge.get("profile_id"),
                    "powertrain_tags": knowledge.get("powertrain_tags", []),
                }
            )

    vehicle_profiles.sort(key=lambda row: (row["market"], row["brand"], row["model"], row["year_start"], row["profile_id"]))
    knowledge_sources.sort(key=lambda row: (row["market"], row["brand"], row["model"], row["source_id"]))
    market_variants.sort(key=lambda row: (row["market"], row["popularity_rank"] if "popularity_rank" in row else 999, row["display_name"]))
    popularity_rankings.sort(key=lambda row: (row["market"], row["popularity_rank"], row["market_variant_id"]))

    return BuildResult(
        canonical_models=sorted(canonical_models.values(), key=lambda row: (row["brand"], row["model"], row["canonical_model_id"])),
        market_variants=market_variants,
        popularity_rankings=popularity_rankings,
        vehicle_profiles=vehicle_profiles,
        knowledge_sources=knowledge_sources,
        eval_cases=eval_cases,
    )


def write_outputs(seed_dir: Path, result: BuildResult) -> None:
    write_jsonl(seed_dir / "canonical_models.jsonl", result.canonical_models)
    write_jsonl(seed_dir / "model_market_variants.jsonl", result.market_variants)
    write_jsonl(seed_dir / "model_popularity_rankings.jsonl", result.popularity_rankings)
    write_jsonl(seed_dir / "vehicle_profiles.jsonl", result.vehicle_profiles)
    write_jsonl(seed_dir / "knowledge_sources.jsonl", result.knowledge_sources)
    write_json(seed_dir / "eval_cases.json", result.eval_cases)


def snapshot_payload(result: BuildResult) -> dict[str, Any]:
    return {
        "canonical_models": result.canonical_models,
        "market_variants": result.market_variants,
        "popularity_rankings": result.popularity_rankings,
        "vehicle_profiles": result.vehicle_profiles,
        "knowledge_sources": result.knowledge_sources,
        "eval_cases": result.eval_cases,
    }


def build_diff(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    return {
        "canonical_models_added": diff_by_id(previous.get("canonical_models", []), current.get("canonical_models", []), "canonical_model_id"),
        "market_variants_added": diff_by_id(previous.get("market_variants", []), current.get("market_variants", []), "market_variant_id"),
        "vehicle_profiles_added": diff_by_id(previous.get("vehicle_profiles", []), current.get("vehicle_profiles", []), "profile_id"),
        "knowledge_sources_added": diff_by_id(previous.get("knowledge_sources", []), current.get("knowledge_sources", []), "source_id"),
        "counts": {
            "previous_vehicle_profiles": len(previous.get("vehicle_profiles", [])),
            "current_vehicle_profiles": len(current.get("vehicle_profiles", [])),
            "previous_market_variants": len(previous.get("market_variants", [])),
            "current_market_variants": len(current.get("market_variants", [])),
        },
    }


def diff_by_id(previous_rows: list[dict[str, Any]], current_rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    previous_ids = {str(row[key]) for row in previous_rows}
    return [row for row in current_rows if str(row[key]) not in previous_ids]


def run_build(seed_dir: Path, source_path: Path, market: str, snapshot_dir: Path) -> None:
    source = read_json(source_path)
    result = build_outputs(source, market)
    write_outputs(seed_dir, result)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_name = f"market-catalog-{market.lower()}-latest.json"
    write_json(snapshot_dir / snapshot_name, snapshot_payload(result))
    print(f"Built catalog seed for market={market}")
    print(f"- canonical_models: {len(result.canonical_models)}")
    print(f"- market_variants: {len(result.market_variants)}")
    print(f"- popularity_rankings: {len(result.popularity_rankings)}")
    print(f"- vehicle_profiles: {len(result.vehicle_profiles)}")
    print(f"- knowledge_sources: {len(result.knowledge_sources)}")
    print(f"- eval_cases: {len(result.eval_cases)}")


def run_diff(seed_dir: Path, source_path: Path, market: str, snapshot_dir: Path, report_path: Path | None) -> None:
    source = read_json(source_path)
    result = build_outputs(source, market)
    current = snapshot_payload(result)
    snapshot_name = f"market-catalog-{market.lower()}-latest.json"
    previous_path = snapshot_dir / snapshot_name
    previous = read_json(previous_path) if previous_path.exists() else {}
    diff = build_diff(previous, current)
    output_path = report_path or (snapshot_dir / f"market-catalog-{market.lower()}-diff.json")
    write_json(output_path, diff)
    print(f"Wrote diff report to {output_path}")
    print(json.dumps(diff["counts"], ensure_ascii=True, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or diff market-aware vehicle catalog seed artifacts.")
    parser.add_argument("mode", choices=["build", "diff"])
    parser.add_argument("--market", default="all", choices=["us", "cn", "all"], help="Target market for output generation.")
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--report", type=Path, default=None, help="Optional diff report path.")
    args = parser.parse_args()

    market = args.market.upper()
    if args.mode == "build":
        run_build(args.seed_dir, args.source, market, args.snapshot_dir)
        return
    run_diff(args.seed_dir, args.source, market, args.snapshot_dir, args.report)


if __name__ == "__main__":
    main()
