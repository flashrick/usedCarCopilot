from __future__ import annotations

from datetime import date
from typing import Any


BODY_SEGMENT_BASE = {
    "hatchback": 0.36,
    "sedan": 0.38,
    "suv": 0.43,
}

BRAND_RETENTION = {
    "Toyota": 1.06,
    "Honda": 1.01,
    "Mazda": 0.99,
}

FUEL_RETENTION = {
    "hybrid": 1.08,
    "petrol": 1.0,
    "diesel": 0.96,
    "electric": 1.03,
}

MAINTENANCE_BAND_FACTOR = {
    "low": 1.03,
    "medium": 1.0,
    "medium_high": 0.95,
    "high": 0.9,
}

CONFIDENCE_BY_BAND = {
    "low": "medium",
    "medium": "medium",
    "medium_high": "low",
    "high": "low",
}


def compute_profile_valuation(profile: dict[str, Any], as_of: date | None = None) -> dict[str, Any]:
    valuation_date = as_of or date.today()
    year_end = int(profile["year_end"])
    current_age = max(1, valuation_date.year - year_end)
    base_msrp = int(profile.get("base_msrp_nzd") or 30000)
    body_type = normalize_text(profile.get("body_type"))
    fuel_type = normalize_text(profile.get("fuel_type"))
    maintenance_band = normalize_text(profile.get("maintenance_cost_band"))

    base_retained = BODY_SEGMENT_BASE.get(body_type, 0.38)
    age_penalty = max(0.42, 1 - (current_age * 0.045))
    brand_factor = BRAND_RETENTION.get(str(profile.get("brand")), 1.0)
    fuel_factor = fuel_retention_factor(fuel_type)
    maintenance_factor = MAINTENANCE_BAND_FACTOR.get(maintenance_band, 1.0)
    reliability_factor = reliability_factor_from_summary(profile.get("reliability_summary"))
    trim_factor = trim_factor_from_profile(profile)
    economy_factor = economy_factor_from_consumption(profile.get("fuel_consumption_l_per_100km"))
    desirability_factor = desirability_factor_from_suitability(profile.get("suitability_summary"))

    midpoint = base_msrp * base_retained
    midpoint *= age_penalty
    midpoint *= brand_factor
    midpoint *= fuel_factor
    midpoint *= maintenance_factor
    midpoint *= reliability_factor
    midpoint *= trim_factor
    midpoint *= economy_factor
    midpoint *= desirability_factor
    midpoint = max(4500, round_to_500(midpoint))

    expected_annual_km = annual_km_for_profile(profile)
    assumed_mileage = current_age * expected_annual_km

    spread = 0.12
    if maintenance_band in {"medium_high", "high"}:
        spread += 0.04
    if fuel_type == "hybrid":
        spread += 0.01

    minimum = max(3000, round_to_500(midpoint * (1 - spread)))
    maximum = round_to_500(midpoint * (1 + spread))
    if maximum < midpoint:
        maximum = midpoint
    if minimum > midpoint:
        minimum = midpoint

    confidence = CONFIDENCE_BY_BAND.get(maintenance_band, "medium")
    if current_age >= 10:
        confidence = "low" if confidence == "medium" else confidence

    notes = (
        "Estimated for a normal-condition NZ used example with age-normalized mileage. "
        "This is a guidance range, not a live asking price."
    )

    return {
        "estimated_price_min_nzd": minimum,
        "estimated_price_mid_nzd": midpoint,
        "estimated_price_max_nzd": maximum,
        "valuation_confidence": confidence,
        "valuation_market": "NZ",
        "valuation_as_of_date": valuation_date,
        "assumed_condition": "good used condition",
        "assumed_mileage_km": assumed_mileage,
        "valuation_method": "deterministic_retained_value_v1",
        "valuation_notes": notes,
    }


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def fuel_retention_factor(fuel_type: str) -> float:
    if "hybrid" in fuel_type:
        return FUEL_RETENTION["hybrid"]
    if "diesel" in fuel_type:
        return FUEL_RETENTION["diesel"]
    if "electric" in fuel_type:
        return FUEL_RETENTION["electric"]
    return FUEL_RETENTION["petrol"]


def reliability_factor_from_summary(summary: Any) -> float:
    text = normalize_text(summary)
    if any(token in text for token in ("strong", "reliable", "robust", "proven")):
        return 1.03
    if any(token in text for token in ("mixed", "careful", "sensitive")):
        return 0.98
    return 1.0


def trim_factor_from_profile(profile: dict[str, Any]) -> float:
    title = f"{profile.get('title', '')} {profile.get('trim', '')}".lower()
    if any(token in title for token in ("ltd", "limited", "rs", "sp25", "gxl", "premium")):
        return 1.05
    if any(token in title for token in ("gx", "base", "s")):
        return 0.98
    return 1.0


def economy_factor_from_consumption(consumption: Any) -> float:
    if consumption is None:
        return 1.0
    value = float(consumption)
    if value <= 4.5:
        return 1.06
    if value <= 6.0:
        return 1.03
    if value >= 8.5:
        return 0.96
    return 1.0


def desirability_factor_from_suitability(summary: Any) -> float:
    text = str(summary or "").lower()
    if any(token in text for token in ("commute", "city", "family", "practical", "easy to park")):
        return 1.02
    if "niche" in text:
        return 0.98
    return 1.0


def annual_km_for_profile(profile: dict[str, Any]) -> int:
    body = normalize_text(profile.get("body_type"))
    fuel = normalize_text(profile.get("fuel_type"))
    base = 12000
    if body == "suv":
        base += 2000
    if "hybrid" in fuel:
        base += 1000
    return base


def round_to_500(value: float) -> int:
    return int(round(value / 500.0) * 500)
