#!/usr/bin/env python3
"""Validate the seed dataset before ingestion and retrieval work."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


LISTING_REQUIRED_FIELDS = {
    "listing_id",
    "title",
    "brand",
    "model",
    "year",
    "price",
    "mileage",
    "transmission",
    "fuel_type",
    "seller_type",
    "location",
    "body_type",
    "source",
    "description",
}

KNOWLEDGE_REQUIRED_FIELDS = {
    "source_id",
    "source_type",
    "source_channel",
    "title",
    "brand",
    "model",
    "year_range",
    "market",
    "tags",
    "summary",
    "text",
    "evidence_level",
    "ownership_stage",
}

TARGET_MODELS = {
    "Toyota Aqua",
    "Toyota Prius",
    "Toyota RAV4",
    "Honda Fit",
    "Honda Civic",
    "Honda HR-V",
    "Mazda Mazda2",
    "Mazda Mazda3",
    "Mazda CX-5",
}

MODEL_ALIASES = {
    "CX-5": "Mazda CX-5",
    "Mazda CX-5": "Mazda CX-5",
    "Mazda2": "Mazda Mazda2",
    "Mazda Mazda2": "Mazda Mazda2",
    "Mazda3": "Mazda Mazda3",
    "Mazda Mazda3": "Mazda Mazda3",
    "Toyota Aqua": "Toyota Aqua",
    "Toyota Prius": "Toyota Prius",
    "Toyota RAV4": "Toyota RAV4",
    "Toyota Corolla": "Toyota Corolla",
    "Honda Fit": "Honda Fit",
    "Honda Civic": "Honda Civic",
    "Honda HR-V": "Honda HR-V",
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
    if brand == "Mazda" and model in {"Mazda2", "Mazda3", "CX-5"}:
        return f"{brand} {model}"
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


def validate_listings(rows: list[dict[str, Any]]) -> tuple[list[str], set[str]]:
    errors = validate_required_fields(rows, LISTING_REQUIRED_FIELDS, "listing")
    ids = [row.get("listing_id") for row in rows]
    for listing_id, count in Counter(ids).items():
        if listing_id and count > 1:
            errors.append(f"listing_id is duplicated: {listing_id}")

    models: set[str] = set()
    for row in rows:
        models.add(full_model_name(row.get("brand"), row.get("model")))
        if row.get("price") is not None and not isinstance(row.get("price"), int):
            errors.append(f"{row.get('listing_id')}: price must be an integer or null")
        if row.get("mileage") is not None and not isinstance(row.get("mileage"), int):
            errors.append(f"{row.get('listing_id')}: mileage must be an integer or null")
        if row.get("description") == "There are no comments":
            errors.append(f"{row.get('listing_id')}: placeholder description was not normalized")
    return errors, models


def validate_knowledge(rows: list[dict[str, Any]]) -> tuple[list[str], set[str]]:
    errors = validate_required_fields(rows, KNOWLEDGE_REQUIRED_FIELDS, "knowledge")
    ids = [row.get("source_id") for row in rows]
    for source_id, count in Counter(ids).items():
        if source_id and count > 1:
            errors.append(f"source_id is duplicated: {source_id}")

    models: set[str] = set()
    for row in rows:
        models.add(full_model_name(row.get("brand"), row.get("model")))
        if not isinstance(row.get("tags"), list) or not row.get("tags"):
            errors.append(f"{row.get('source_id')}: tags must be a non-empty list")
        text = row.get("text")
        if not isinstance(text, str) or len(text.split()) < 12:
            errors.append(f"{row.get('source_id')}: text is too short to be useful for retrieval")
    return errors, models


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


def validate_eval_cases(cases: Any, listing_models: set[str], knowledge_models: set[str]) -> tuple[list[str], list[str]]:
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
        for field in ("id", "query", "expected_filters", "expected_candidate_models", "expected_risk_themes"):
            if field not in case:
                errors.append(f"eval case {case.get('id', index)}: missing {field}")
        if not isinstance(case.get("query"), str) or len(case["query"].split()) < 4:
            errors.append(f"eval case {case.get('id', index)}: query is too short")

    referenced_models = collect_eval_models(cases)
    available_models = listing_models | knowledge_models
    missing_models = sorted(model for model in referenced_models if model not in available_models)
    if missing_models:
        errors.append("eval references models missing from seed listings and knowledge: " + ", ".join(missing_models))

    missing_listing_models = sorted(
        model for model in referenced_models if model in knowledge_models and model not in listing_models
    )
    if missing_listing_models:
        warnings.append("eval references models with knowledge but no listing rows: " + ", ".join(missing_listing_models))

    missing_target_listings = sorted(model for model in TARGET_MODELS if model not in listing_models)
    if missing_target_listings:
        warnings.append("target MVP models missing listing rows: " + ", ".join(missing_target_listings))

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listings", type=Path, default=Path("data/seed/listings.jsonl"))
    parser.add_argument("--knowledge", type=Path, default=Path("data/seed/knowledge_sources.jsonl"))
    parser.add_argument("--eval-cases", type=Path, default=Path("data/seed/eval_cases.json"))
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    listing_errors, listing_models = validate_listings(read_jsonl(args.listings))
    knowledge_errors, knowledge_models = validate_knowledge(read_jsonl(args.knowledge))
    errors.extend(listing_errors)
    errors.extend(knowledge_errors)
    eval_errors, eval_warnings = validate_eval_cases(read_json(args.eval_cases), listing_models, knowledge_models)
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
    print(f"- listing models: {', '.join(sorted(listing_models))}")
    print(f"- knowledge models: {', '.join(sorted(knowledge_models))}")


if __name__ == "__main__":
    main()
