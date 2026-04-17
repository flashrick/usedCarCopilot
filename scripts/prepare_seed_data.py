#!/usr/bin/env python3
"""Normalize raw listing data into seed data used by the MVP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


MODEL_ALIASES = {
    "FIT": "Fit",
    "Fit": "Fit",
    "HR-V": "HR-V",
    "CX-5": "CX-5",
    "Mazda2": "Mazda2",
    "Mazda3": "Mazda3",
    "Aqua": "Aqua",
    "Prius": "Prius",
    "Rav4": "RAV4",
    "RAV4": "RAV4",
}

BODY_TYPE_BY_MODEL = {
    "Aqua": "hatchback",
    "Prius": "hatchback",
    "RAV4": "suv",
    "Fit": "hatchback",
    "Civic": "sedan",
    "HR-V": "suv",
    "Mazda2": "hatchback",
    "Mazda3": "hatchback",
    "CX-5": "suv",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise SystemExit(f"{path}:{line_number}: expected a JSON object")
        rows.append(value)
    return rows


def canonical_model(model: Any) -> str:
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be a non-empty string")
    stripped = model.strip()
    return MODEL_ALIASES.get(stripped, stripped)


def canonical_transmission(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text == "constantly variable transmission":
        return "cvt"
    return text


def normalize_listing(row: dict[str, Any]) -> dict[str, Any]:
    model = canonical_model(row.get("model"))
    description = row.get("description")
    if description == "There are no comments":
        description = None

    return {
        "listing_id": row["listing_id"],
        "title": row["title"],
        "brand": row["brand"],
        "model": model,
        "year": row.get("year"),
        "price": row.get("price"),
        "mileage": row.get("mileage"),
        "transmission": canonical_transmission(row.get("transmission")),
        "fuel_type": row.get("fuel_type"),
        "seller_type": row.get("seller_type"),
        "location": row.get("location"),
        "body_type": BODY_TYPE_BY_MODEL.get(model),
        "source": "turners",
        "source_url": row.get("source_url"),
        "description": description,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            file.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/raw/turners_listings.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("data/seed/listings.jsonl"))
    args = parser.parse_args()

    rows = [normalize_listing(row) for row in read_jsonl(args.input)]
    rows.sort(key=lambda row: (row["brand"], row["model"], row["price"] is None, row["price"] or 0, row["year"] or 0))
    write_jsonl(args.output, rows)
    print(f"Wrote {len(rows)} normalized listings to {args.output}")


if __name__ == "__main__":
    main()
