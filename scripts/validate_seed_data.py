#!/usr/bin/env python3
"""Validate the market-aware seed dataset used by retrieval and recommendation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.valuation.service import compute_profile_valuation


CANONICAL_MODEL_REQUIRED_FIELDS = {
    "canonical_model_id",
    "brand",
    "model",
    "canonical_model_slug",
    "aliases",
}

MARKET_VARIANT_REQUIRED_FIELDS = {
    "market_variant_id",
    "canonical_model_id",
    "market",
    "brand",
    "model",
    "display_name",
    "year_start",
    "year_end",
    "body_types",
    "fuel_types",
}

POPULARITY_REQUIRED_FIELDS = {
    "market",
    "market_variant_id",
    "popularity_rank",
    "brand_popularity_rank",
    "source_label",
    "snapshot_date",
    "match_tags",
}

PROFILE_REQUIRED_FIELDS = {
    "profile_id",
    "title",
    "brand",
    "model",
    "market",
    "market_variant_id",
    "year_start",
    "year_end",
    "trim",
    "engine_description",
    "transmission",
    "fuel_type",
    "body_type",
    "fuel_consumption_l_per_100km",
    "nvh_summary",
    "comfort_summary",
    "space_summary",
    "reliability_summary",
    "common_issues",
    "maintenance_cost_band",
    "suitability_summary",
    "base_msrp_nzd",
}

KNOWLEDGE_REQUIRED_FIELDS = {
    "source_id",
    "source_type",
    "source_channel",
    "title",
    "brand",
    "model",
    "market",
    "market_variant_id",
    "year_range",
    "tags",
    "summary",
    "text",
    "evidence_level",
    "ownership_stage",
}

SAFETY_REQUIRED_FIELDS = {
    "profile_id",
    "market_variant_id",
    "market",
    "brand",
    "model",
    "year_start",
    "year_end",
    "safety_rating_stars",
    "safety_rating_source",
    "safety_rating_status",
}

MODEL_ALIASES = {
    "Toyota RAV4": "Toyota RAV4",
    "Honda CR-V": "Honda CR-V",
    "Toyota Camry": "Toyota Camry",
    "Honda Civic": "Honda Civic",
    "Tesla Model Y": "Tesla Model Y",
    "BYD Song Plus": "BYD Song Plus",
    "BYD Qin Plus": "BYD Qin Plus",
    "RAV4": "Toyota RAV4",
    "CR-V": "Honda CR-V",
    "Camry": "Toyota Camry",
    "Civic": "Honda Civic",
    "Model Y": "Tesla Model Y",
    "Song Plus": "BYD Song Plus",
    "Qin Plus": "BYD Qin Plus",
}


class ValidationError(Exception):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise ValidationError(f"{path}:{line_number}: expected a JSON object")
        rows.append(value)
    return rows


def full_model_name(brand: Any, model: Any) -> str:
    if not isinstance(brand, str) or not isinstance(model, str):
        return ""
    return f"{brand} {model}"


def canonical_eval_model(value: str) -> str:
    return MODEL_ALIASES.get(value, value)


def validate_required_fields(rows: list[dict[str, Any]], required: set[str], label: str) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"{label} row {index}: missing fields: {', '.join(missing)}")
    return errors


def validate_canonical_models(rows: list[dict[str, Any]]) -> tuple[list[str], set[str]]:
    errors = validate_required_fields(rows, CANONICAL_MODEL_REQUIRED_FIELDS, "canonical model")
    ids = [row.get("canonical_model_id") for row in rows]
    for model_id, count in Counter(ids).items():
        if model_id and count > 1:
            errors.append(f"canonical_model_id is duplicated: {model_id}")
    return errors, {str(row["canonical_model_id"]) for row in rows if row.get("canonical_model_id")}


def validate_market_variants(rows: list[dict[str, Any]], canonical_model_ids: set[str]) -> tuple[list[str], set[str], set[str]]:
    errors = validate_required_fields(rows, MARKET_VARIANT_REQUIRED_FIELDS, "market variant")
    ids = [row.get("market_variant_id") for row in rows]
    display_names_by_market: set[tuple[str, str]] = set()
    variant_ids: set[str] = set()
    models: set[str] = set()

    for variant_id, count in Counter(ids).items():
        if variant_id and count > 1:
            errors.append(f"market_variant_id is duplicated: {variant_id}")

    for row in rows:
        variant_id = str(row.get("market_variant_id"))
        variant_ids.add(variant_id)
        models.add(full_model_name(row.get("brand"), row.get("model")))
        if row.get("canonical_model_id") not in canonical_model_ids:
            errors.append(f"{variant_id}: canonical_model_id does not exist in canonical_models.jsonl")
        if row.get("market") not in {"US", "CN"}:
            errors.append(f"{variant_id}: market must be US or CN")
        if row.get("year_end") < row.get("year_start"):
            errors.append(f"{variant_id}: year_end must be >= year_start")
        display_key = (str(row.get("market")), str(row.get("display_name")))
        if display_key in display_names_by_market:
            errors.append(f"display_name is duplicated within market: {display_key[0]} {display_key[1]}")
        display_names_by_market.add(display_key)
    return errors, variant_ids, models


def validate_popularity_rankings(rows: list[dict[str, Any]], market_variant_ids: set[str]) -> list[str]:
    errors = validate_required_fields(rows, POPULARITY_REQUIRED_FIELDS, "popularity ranking")
    seen_ranks: set[tuple[str, int]] = set()
    for row in rows:
        variant_id = str(row.get("market_variant_id"))
        if variant_id not in market_variant_ids:
            errors.append(f"{variant_id}: popularity ranking market_variant_id does not exist")
        if row.get("market") not in {"US", "CN"}:
            errors.append(f"{variant_id}: popularity ranking market must be US or CN")
        try:
            rank_key = (str(row.get("market")), int(row.get("popularity_rank")))
        except (TypeError, ValueError):
            errors.append(f"{variant_id}: popularity_rank must be an integer")
            continue
        if rank_key in seen_ranks:
            errors.append(f"popularity_rank is duplicated within market: {rank_key[0]} rank {rank_key[1]}")
        seen_ranks.add(rank_key)
    return errors


def validate_vehicle_profiles(rows: list[dict[str, Any]], market_variant_ids: set[str]) -> tuple[list[str], set[str]]:
    errors = validate_required_fields(rows, PROFILE_REQUIRED_FIELDS, "vehicle profile")
    ids = [row.get("profile_id") for row in rows]
    for profile_id, count in Counter(ids).items():
        if profile_id and count > 1:
            errors.append(f"profile_id is duplicated: {profile_id}")

    models: set[str] = set()
    for row in rows:
        models.add(full_model_name(row.get("brand"), row.get("model")))
        if row.get("market") not in {"US", "CN"}:
            errors.append(f"{row.get('profile_id')}: market must be US or CN")
        if row.get("market_variant_id") not in market_variant_ids:
            errors.append(f"{row.get('profile_id')}: market_variant_id does not exist in model_market_variants.jsonl")
        if not isinstance(row.get("common_issues"), list) or not row.get("common_issues"):
            errors.append(f"{row.get('profile_id')}: common_issues must be a non-empty list")
        if not isinstance(row.get("base_msrp_nzd"), int) or row["base_msrp_nzd"] <= 0:
            errors.append(f"{row.get('profile_id')}: base_msrp_nzd must be a positive integer")
        if row.get("year_end") < row.get("year_start"):
            errors.append(f"{row.get('profile_id')}: year_end must be >= year_start")
        try:
            valuation = compute_profile_valuation(row)
        except Exception as exc:
            errors.append(f"{row.get('profile_id')}: valuation failed: {exc}")
            continue
        minimum = valuation["estimated_price_min_nzd"]
        midpoint = valuation["estimated_price_mid_nzd"]
        maximum = valuation["estimated_price_max_nzd"]
        if not (minimum <= midpoint <= maximum):
            errors.append(f"{row.get('profile_id')}: valuation range is not monotonic")
        if valuation["assumed_mileage_km"] <= 0:
            errors.append(f"{row.get('profile_id')}: assumed mileage must be positive")
    return errors, models


def validate_knowledge(rows: list[dict[str, Any]], profile_ids: set[str], market_variant_ids: set[str]) -> tuple[list[str], set[str]]:
    errors = validate_required_fields(rows, KNOWLEDGE_REQUIRED_FIELDS, "knowledge")
    ids = [row.get("source_id") for row in rows]
    for source_id, count in Counter(ids).items():
        if source_id and count > 1:
            errors.append(f"source_id is duplicated: {source_id}")

    models: set[str] = set()
    for row in rows:
        models.add(full_model_name(row.get("brand"), row.get("model")))
        if row.get("market") not in {"US", "CN"}:
            errors.append(f"{row.get('source_id')}: market must be US or CN")
        if row.get("market_variant_id") not in market_variant_ids:
            errors.append(f"{row.get('source_id')}: market_variant_id does not exist in model_market_variants.jsonl")
        if not isinstance(row.get("tags"), list) or not row.get("tags"):
            errors.append(f"{row.get('source_id')}: tags must be a non-empty list")
        text = row.get("text")
        if not isinstance(text, str) or len(text.split()) < 12:
            errors.append(f"{row.get('source_id')}: text is too short to be useful for retrieval")
        linked_profile_id = row.get("profile_id")
        if linked_profile_id and linked_profile_id not in profile_ids:
            errors.append(f"{row.get('source_id')}: profile_id does not exist in vehicle_profiles.jsonl")
    return errors, models


def validate_safety_ratings(
    rows: list[dict[str, Any]],
    profile_ids: set[str],
    market_variant_ids: set[str],
) -> list[str]:
    errors = validate_required_fields(rows, SAFETY_REQUIRED_FIELDS, "safety rating")
    ids = [row.get("profile_id") for row in rows]
    for profile_id, count in Counter(ids).items():
        if profile_id and count > 1:
            errors.append(f"safety rating profile_id is duplicated: {profile_id}")

    for row in rows:
        profile_id = row.get("profile_id")
        status = row.get("safety_rating_status")
        stars = row.get("safety_rating_stars")
        source = row.get("safety_rating_source")
        if row.get("market") not in {"US", "CN"}:
            errors.append(f"{profile_id}: safety rating market must be US or CN")
        if row.get("market_variant_id") not in market_variant_ids:
            errors.append(f"{profile_id}: safety rating market_variant_id does not exist in model_market_variants.jsonl")
        if profile_id not in profile_ids:
            errors.append(f"{profile_id}: safety rating profile_id does not exist in vehicle_profiles.jsonl")
        if status not in {"rated", "unrated"}:
            errors.append(f"{profile_id}: safety_rating_status must be rated or unrated")
        if row.get("year_end") < row.get("year_start"):
            errors.append(f"{profile_id}: safety rating year_end must be >= year_start")
        if status == "rated":
            if not isinstance(stars, int) or not (1 <= stars <= 5):
                errors.append(f"{profile_id}: rated safety rows must have integer stars between 1 and 5")
            if not isinstance(source, str) or not source.strip():
                errors.append(f"{profile_id}: rated safety rows must have a non-empty source")
        if status == "unrated":
            if stars is not None:
                errors.append(f"{profile_id}: unrated safety rows must not include stars")
            if source is not None:
                errors.append(f"{profile_id}: unrated safety rows must not include a source")
    return errors


def collect_eval_models(value: Any) -> set[str]:
    models: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"model", "expected_candidate_models", "compare_models"}:
                if isinstance(nested, str):
                    models.add(canonical_eval_model(nested))
                elif isinstance(nested, list):
                    models.update(canonical_eval_model(item) for item in nested if isinstance(item, str))
            else:
                models.update(collect_eval_models(nested))
    elif isinstance(value, list):
        for item in value:
            models.update(collect_eval_models(item))
    return models


def validate_eval_cases(cases: Any, profile_models: set[str], knowledge_models: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(cases, list):
        return ["eval cases file must contain a JSON array"], warnings

    ids = [case.get("id") for case in cases if isinstance(case, dict)]
    for case_id, count in Counter(ids).items():
        if case_id and count > 1:
            errors.append(f"eval id is duplicated: {case_id}")

    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"eval case {index}: expected an object")
            continue
        for field in ("id", "market", "query", "expected_filters", "expected_candidate_models", "expected_risk_themes"):
            if field not in case:
                errors.append(f"eval case {case.get('id', index)}: missing {field}")
        if case.get("market") not in {"US", "CN"}:
            errors.append(f"eval case {case.get('id', index)}: market must be US or CN")
        if not isinstance(case.get("query"), str) or len(case["query"]) < 8:
            errors.append(f"eval case {case.get('id', index)}: query is too short")

    referenced_models = collect_eval_models(cases)
    available_models = profile_models | knowledge_models
    missing_models = sorted(model for model in referenced_models if model not in available_models)
    if missing_models:
        errors.append("eval references models missing from vehicle profiles and knowledge: " + ", ".join(missing_models))
    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-models", type=Path, default=Path("data/seed/canonical_models.jsonl"))
    parser.add_argument("--market-variants", type=Path, default=Path("data/seed/model_market_variants.jsonl"))
    parser.add_argument("--popularity", type=Path, default=Path("data/seed/model_popularity_rankings.jsonl"))
    parser.add_argument("--vehicle-profiles", type=Path, default=Path("data/seed/vehicle_profiles.jsonl"))
    parser.add_argument("--knowledge", type=Path, default=Path("data/seed/knowledge_sources.jsonl"))
    parser.add_argument("--safety-ratings", type=Path, default=Path("data/seed/safety_ratings.jsonl"))
    parser.add_argument("--eval-cases", type=Path, default=Path("data/seed/eval_cases.json"))
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    canonical_errors, canonical_model_ids = validate_canonical_models(read_jsonl(args.canonical_models))
    variant_errors, market_variant_ids, variant_models = validate_market_variants(read_jsonl(args.market_variants), canonical_model_ids)
    popularity_errors = validate_popularity_rankings(read_jsonl(args.popularity), market_variant_ids)
    profile_rows = read_jsonl(args.vehicle_profiles)
    profile_errors, profile_models = validate_vehicle_profiles(profile_rows, market_variant_ids)
    profile_ids = {row["profile_id"] for row in profile_rows if row.get("profile_id")}
    knowledge_errors, knowledge_models = validate_knowledge(read_jsonl(args.knowledge), profile_ids, market_variant_ids)
    safety_errors = validate_safety_ratings(read_jsonl(args.safety_ratings), profile_ids, market_variant_ids)
    eval_errors, eval_warnings = validate_eval_cases(read_json(args.eval_cases), profile_models | variant_models, knowledge_models | variant_models)

    errors.extend(canonical_errors)
    errors.extend(variant_errors)
    errors.extend(popularity_errors)
    errors.extend(profile_errors)
    errors.extend(knowledge_errors)
    errors.extend(safety_errors)
    errors.extend(eval_errors)
    warnings.extend(eval_warnings)

    if errors:
        print("Seed data validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Seed data validation passed")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print(f"- vehicle profile models: {', '.join(sorted(profile_models))}")
    print(f"- knowledge models: {', '.join(sorted(knowledge_models))}")


if __name__ == "__main__":
    main()
