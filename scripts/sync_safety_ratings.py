#!/usr/bin/env python3
"""Build and diff market-aware safety-rating seed artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

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
NHTSA_BASE_URL = "https://api.nhtsa.gov/SafetyRatings"
NHTSA_SOURCE_LABEL = "NHTSA SafetyRatings API"

DRIVETRAIN_HINTS = {
    "awd": (" AWD ", " 4WD ", " ALL WHEEL DRIVE ", " FOUR WHEEL DRIVE "),
    "4wd": (" 4WD ", " AWD ", " FOUR WHEEL DRIVE ", " ALL WHEEL DRIVE "),
    "fwd": (" FWD ", " FRONT WHEEL DRIVE "),
    "rwd": (" RWD ", " REAR WHEEL DRIVE "),
}

BODY_TYPE_HINTS = {
    "suv": (" SUV ",),
    "sedan": (" 4 DR ", " SEDAN "),
    "hatchback": (" HATCHBACK ", " 5 DR ", " 3 DR "),
    "wagon": (" WAGON ",),
    "pickup": (" PICKUP ", " TRUCK "),
}

FUEL_HINTS = {
    "petrol hybrid": (" HYBRID ",),
    "diesel hybrid": (" HYBRID ",),
    "phev": (" PHEV ", " PLUG-IN ", " PLUG IN "),
    "ev": (" ELECTRIC ", " EV "),
}


@dataclass(frozen=True)
class BuildResult:
    safety_ratings: list[dict[str, Any]]


def normalize_description(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in value.upper())
    return f" {' '.join(cleaned.split())} "


def model_queries(model: str) -> list[str]:
    queries = [model.strip()]
    compact = model.replace(" ", "").strip()
    if compact and compact not in queries:
        queries.append(compact)
    if " " in model:
        tail = model.split()[-1].strip()
        if tail and tail not in queries:
            queries.append(tail)
    return queries


def parse_overall_rating(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "not rated":
        return None
    if text[0].isdigit():
        score = int(text[0])
        if 1 <= score <= 5:
            return score
    return None


def score_vehicle_match(profile: dict[str, Any], vehicle_description: str) -> tuple[int, str]:
    normalized = normalize_description(vehicle_description)
    score = 0

    drivetrain = str(profile.get("drivetrain", "")).lower()
    for hint in DRIVETRAIN_HINTS.get(drivetrain, ()):
        if hint in normalized:
            score += 8
            break

    body_type = str(profile.get("body_type", "")).lower()
    for hint in BODY_TYPE_HINTS.get(body_type, ()):
        if hint in normalized:
            score += 6
            break

    fuel_type = str(profile.get("fuel_type", "")).lower()
    for hint in FUEL_HINTS.get(fuel_type, ()):
        if hint in normalized:
            score += 3
            break

    trim = str(profile.get("trim", "")).upper()
    for token in trim.replace("-", " ").split():
        if len(token) < 3:
            continue
        if f" {token} " in normalized:
            score += 1

    return score, normalized


def choose_vehicle(profile: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None

    scored: list[tuple[int, int, dict[str, Any]]] = []
    for candidate in candidates:
        score, normalized = score_vehicle_match(profile, str(candidate.get("VehicleDescription", "")))
        scored.append((score, len(normalized), candidate))

    scored.sort(key=lambda item: (item[0], item[1], int(item[2].get("VehicleId", 0))), reverse=True)
    best_score, _, best = scored[0]
    if best_score <= 0 and len(candidates) > 1:
        return None
    return best


class NhtsaApiClient:
    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.Client(
            base_url=NHTSA_BASE_URL,
            timeout=timeout_seconds,
            headers={"User-Agent": "usedCarCopilot/1.0"},
        )
        self._version_cache: dict[tuple[int, str, str], list[dict[str, Any]]] = {}
        self._rating_cache: dict[int, dict[str, Any]] = {}

    def close(self) -> None:
        self._client.close()

    def list_vehicle_versions(self, year: int, make: str, model: str) -> list[dict[str, Any]]:
        cache_key = (year, make.upper(), model.upper())
        if cache_key in self._version_cache:
            return self._version_cache[cache_key]
        path = f"/modelyear/{year}/make/{quote(make, safe='')}/model/{quote(model, safe='')}"
        response = self._client.get(path)
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("Results", [])
        if not isinstance(rows, list):
            raise ValueError(f"Unexpected NHTSA version payload for {year} {make} {model}")
        normalized = [row for row in rows if isinstance(row, dict)]
        self._version_cache[cache_key] = normalized
        return normalized

    def get_vehicle_rating(self, vehicle_id: int) -> dict[str, Any]:
        if vehicle_id in self._rating_cache:
            return self._rating_cache[vehicle_id]
        response = self._client.get(f"/VehicleId/{vehicle_id}")
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("Results", [])
        if not rows or not isinstance(rows[0], dict):
            raise ValueError(f"Unexpected NHTSA rating payload for vehicle_id={vehicle_id}")
        self._rating_cache[vehicle_id] = rows[0]
        return rows[0]


def unrated_row(item: dict[str, Any], profile: dict[str, Any], details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "profile_id": profile["profile_id"],
        "market_variant_id": item["market_variant_id"],
        "market": item["market"],
        "brand": item["brand"],
        "model": item["model"],
        "year_start": profile["year_start"],
        "year_end": profile["year_end"],
        "safety_rating_stars": None,
        "safety_rating_source": None,
        "safety_rating_status": "unrated",
        "nhtsa_rating_details": details or [],
    }


def resolve_us_profile_rating(
    item: dict[str, Any],
    profile: dict[str, Any],
    client: Any,
) -> dict[str, Any]:
    details: list[dict[str, Any]] = []
    numeric_ratings: list[int] = []

    for year in range(int(profile["year_start"]), int(profile["year_end"]) + 1):
        selected_candidate: dict[str, Any] | None = None
        tried_models: list[str] = []

        for model_query in model_queries(str(item["model"])):
            tried_models.append(model_query)
            candidates = client.list_vehicle_versions(year, str(item["brand"]), model_query)
            selected_candidate = choose_vehicle(profile, candidates)
            if selected_candidate is not None:
                break

        if selected_candidate is None:
            details.append(
                {
                    "year": year,
                    "model_queries": tried_models,
                    "lookup_status": "no_match",
                }
            )
            continue

        vehicle_id = int(selected_candidate["VehicleId"])
        rating = client.get_vehicle_rating(vehicle_id)
        overall_rating = rating.get("OverallRating")
        parsed_rating = parse_overall_rating(overall_rating)
        if parsed_rating is not None:
            numeric_ratings.append(parsed_rating)

        details.append(
            {
                "year": year,
                "model_queries": tried_models,
                "lookup_status": "matched",
                "vehicle_id": vehicle_id,
                "vehicle_description": selected_candidate.get("VehicleDescription"),
                "overall_rating": overall_rating,
                "overall_front_crash_rating": rating.get("OverallFrontCrashRating"),
                "overall_side_crash_rating": rating.get("OverallSideCrashRating"),
                "rollover_rating": rating.get("RolloverRating"),
                "complaints_count": rating.get("ComplaintsCount"),
                "recalls_count": rating.get("RecallsCount"),
                "investigation_count": rating.get("InvestigationCount"),
                "electronic_stability_control": rating.get("NHTSAElectronicStabilityControl"),
                "forward_collision_warning": rating.get("NHTSAForwardCollisionWarning"),
                "lane_departure_warning": rating.get("NHTSALaneDepartureWarning"),
            }
        )

    if not numeric_ratings:
        return unrated_row(item, profile, details)

    return {
        "profile_id": profile["profile_id"],
        "market_variant_id": item["market_variant_id"],
        "market": item["market"],
        "brand": item["brand"],
        "model": item["model"],
        "year_start": profile["year_start"],
        "year_end": profile["year_end"],
        "safety_rating_stars": min(numeric_ratings),
        "safety_rating_source": NHTSA_SOURCE_LABEL,
        "safety_rating_status": "rated",
        "nhtsa_rating_details": details,
    }


def build_outputs(source: dict[str, Any], market: str, client: Any | None = None) -> BuildResult:
    safety_ratings: list[dict[str, Any]] = []
    owned_client = False

    if client is None and market in {"US", "ALL"}:
        client = NhtsaApiClient()
        owned_client = True

    try:
        for item in list(source.get("models", [])):
            item_market = str(item.get("market", "")).upper()
            if market != "ALL" and item_market != market:
                continue
            for profile in item.get("profiles", []):
                if item_market != "US":
                    safety_ratings.append(unrated_row(item, profile))
                    continue
                if client is None:
                    raise ValueError("NHTSA client is required for US safety sync")
                safety_ratings.append(resolve_us_profile_rating(item, profile, client))
    finally:
        if owned_client and hasattr(client, "close"):
            client.close()

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
